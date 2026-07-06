frappe.pages['vectorizar-patron'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Vectorizar Imagen',
		single_column: true,
	});
	$(frappe.render_template('vectorizar_patron', {})).appendTo(page.body);
	page.set_secondary_action(__('Administrar Patrones'), () => frappe.set_route('admin-patrones'));
	new Vectorizador(page);
};

class Vectorizador {
	constructor(page) {
		this.page = page;
		this.file_url = null;
		this.file_label = null;
		this.run_id = null;
		this.presets = [];        // r.message.presets — [{name, slug, viewbox, svg_full, entities, entity_count}]
		this.preset_idx = null;   // preset elegido

		// Estado del visor (por preset elegido)
		this.svgEl = null;
		this.viewBox = null;      // {x,y,w,h} actual
		this.origViewBox = null;  // para "Reset vista"
		this.mode = 'select';     // 'select' | 'calibrate' | 'pan'
		this.calibArm = null;     // 'v' | 'h' | null — qué línea se está por dibujar
		this.calib = { vLine: null, hLine: null, vMm: null, escala_display: null };

		// drag/rubber-band/pan state
		this._drag = null;

		// Paso 4 — preset por figura (PUNTO_PRESET_POR_FIGURA, MSG_033 de Punto).
		// entityOverrides: { [sourceEntityId]: { preset, entity_id } } — solo
		// entradas para figuras que el usuario cambió del preset global; las que
		// no están acá usan el preset del paso 2 tal cual.
		this.entityOverrides = {};
		this._presetSvgCache = {};   // preset.name -> <svg> ya parseado (para no reparsear svg_full)

		this.make_customer_control();
		this.bind_events();
		this.setup_paste_and_drop();
	}

	make_customer_control() {
		this.customer_control = frappe.ui.form.make_control({
			df: { fieldtype: 'Link', options: 'Customer', fieldname: 'cliente', placeholder: __('Cliente') },
			parent: $('#vp-customer-field'),
			render_input: true,
		});
	}
	get_customer() {
		return (this.customer_control && this.customer_control.get_value()) || '';
	}

	bind_events() {
		$('#vp-drop').on('click', () => this.pick_image());
		$('#vp-btn-vectorizar').on('click', () => this.vectorizar());
		$('#vp-btn-crear').on('click', () => this.crear());
		$('#vp-visibilidad').on('change', () => {
			const excl = $('#vp-visibilidad').val() === 'Exclusivo';
			$('#vp-customer-group').toggleClass('hidden', !excl);
		});

		$('.vp-tool').on('click', (e) => this.set_mode($(e.currentTarget).data('mode')));
		$('#vp-zoom-in').on('click', () => this.zoom_by(0.8));
		$('#vp-zoom-out').on('click', () => this.zoom_by(1.25));
		$('#vp-zoom-reset').on('click', () => this.reset_view());
		$('#vp-select-all').on('click', () => this.select_all(true));
		$('#vp-select-none').on('click', () => this.select_all(false));

		$('#vp-calib-btn-v').on('click', () => this.arm_calib_line('v'));
		$('#vp-calib-btn-h').on('click', () => this.arm_calib_line('h'));
		$('#vp-calib-apply').on('click', () => this.apply_calibration());
	}

	// ------------------------------------------------------------------
	// Paso 1 — subir imagen (file picker, Ctrl+V, drag&drop)
	// ------------------------------------------------------------------

	pick_image() {
		new frappe.ui.FileUploader({
			as_dataurl: false,
			allow_multiple: false,
			restrictions: { allowed_file_types: ['image/*', '.png', '.jpg', '.jpeg'] },
			make_attachments_public: false,
			on_success: (file_doc) => this.set_image_from_file_doc(file_doc),
		});
	}

	set_image_from_file_doc(file_doc) {
		this.file_url = file_doc.file_url;
		this.file_label = file_doc.file_name || file_doc.file_url;
		$('#vp-drop-prompt').addClass('hidden');
		$('#vp-file-name').removeClass('hidden').text('✓ ' + this.file_label);
		$('#vp-drop').addClass('has-file');
		$('#vp-file-preview').attr('src', this.file_url).removeClass('hidden');
		$('#vp-btn-vectorizar').prop('disabled', false);
	}

	// Zona de pegado propia (no pasa por el FileUploader de Frappe, que no
	// captura 'paste' de fábrica). Sube el blob directo con /api/method/upload_file.
	setup_paste_and_drop() {
		const drop = document.getElementById('vp-drop');

		document.addEventListener('paste', (e) => {
			const tag = (e.target.tagName || '').toLowerCase();
			if (tag === 'input' || tag === 'textarea' || tag === 'select') return; // no interferir con inputs
			const items = (e.clipboardData && e.clipboardData.items) || [];
			const item = [...items].find((i) => i.type && i.type.startsWith('image/'));
			if (!item) return;
			e.preventDefault();
			const blob = item.getAsFile();
			this.upload_blob(blob, 'pegado.png');
		});

		drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('drag-over'); });
		drop.addEventListener('dragleave', () => drop.classList.remove('drag-over'));
		drop.addEventListener('drop', (e) => {
			e.preventDefault();
			e.stopPropagation();
			drop.classList.remove('drag-over');
			const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
			if (file && file.type.startsWith('image/')) this.upload_blob(file, file.name);
		});
	}

	async upload_blob(blob, filename) {
		const status = $('#vp-status').css('color', '').text(__('Subiendo imagen…'));
		try {
			const fd = new FormData();
			fd.append('file', blob, filename);
			fd.append('is_private', 1);
			const resp = await fetch('/api/method/upload_file', {
				method: 'POST',
				headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
				body: fd,
			});
			if (!resp.ok) throw new Error('HTTP ' + resp.status);
			const data = await resp.json();
			const file_doc = data.message;
			this.set_image_from_file_doc(file_doc);
			status.text('');
		} catch (e) {
			status.css('color', 'var(--si-red)').text(__('Error al subir la imagen pegada/soltada.'));
		}
	}

	// ------------------------------------------------------------------
	// Paso 1 → 2 — vectorizar
	// ------------------------------------------------------------------

	vectorizar() {
		if (!this.file_url) return;
		const status = $('#vp-status').css('color', '').text('');
		$('#vp-spinner').removeClass('hidden');
		$('#vp-btn-vectorizar').prop('disabled', true);
		$('#vp-section-presets').addClass('hidden');
		$('#vp-section-visor').addClass('hidden');
		$('#vp-section-confirmar').addClass('hidden');

		frappe.call({
			method: 'sistema_industrial.api.vectorizer.vectorize_image',
			args: { file_url: this.file_url },
			callback: (r) => {
				const m = r.message || {};
				this.run_id = m.run_id || null;
				this.presets = m.presets || [];
				if (!this.run_id || !this.presets.length) {
					status.css('color', 'var(--si-red)')
						.text(__('No se detectaron entidades en la imagen. Probá con otra imagen.'));
					return;
				}
				this.preset_idx = null;
				this.render_presets();
				$('#vp-section-presets').removeClass('hidden');
			},
			error: () => {
				status.css('color', 'var(--si-red)')
					.text(__('Error al vectorizar. Revisá que la imagen sea válida y volvé a intentar.'));
			},
			always: () => {
				$('#vp-spinner').addClass('hidden');
				$('#vp-btn-vectorizar').prop('disabled', false);
			},
		});
	}

	// ------------------------------------------------------------------
	// Paso 2 — elegir preset
	// ------------------------------------------------------------------

	render_presets() {
		const grid = $('#vp-preset-grid').empty();
		this.presets.forEach((p, i) => {
			const card = $('<div class="vp-preset-card">').attr('data-idx', i);
			const thumb = $('<div class="vp-preset-thumb">');
			thumb.html(p.svg_full || '');
			card.append(thumb);
			card.append($('<div class="vp-preset-name">').text(p.name));
			card.append($('<div class="vp-preset-count">').text((p.entity_count || 0) + ' ' + __('entidades')));
			card.on('click', () => this.select_preset(i));
			grid.append(card);
		});
	}

	select_preset(idx) {
		this.preset_idx = idx;
		$('#vp-preset-grid .vp-preset-card').removeClass('selected');
		$('#vp-preset-grid .vp-preset-card[data-idx="' + idx + '"]').addClass('selected');

		// Cambiar de preset resetea selección, calibración y overrides por
		// figura (los entity_id del preset viejo ya no significan nada acá).
		this.calib = { vLine: null, hLine: null, vMm: null, escala_display: null };
		this.calibArm = null;
		this.entityOverrides = {};
		this.set_mode('select');

		const preset = this.presets[idx];
		const viewer = document.getElementById('vp-viewer');
		viewer.innerHTML = preset.svg_full || '';
		this.svgEl = viewer.querySelector('svg');
		if (this.svgEl) {
			const vb = this.svgEl.getAttribute('viewBox');
			if (vb) {
				const [x, y, w, h] = vb.split(/\s+/).map(Number);
				this.viewBox = { x, y, w, h };
			} else {
				const bw = parseFloat(this.svgEl.getAttribute('width')) || 100;
				const bh = parseFloat(this.svgEl.getAttribute('height')) || 100;
				this.viewBox = { x: 0, y: 0, w: bw, h: bh };
			}
			this.origViewBox = Object.assign({}, this.viewBox);
			this.apply_viewbox();
			this.wire_viewer_events();
		}

		this.update_calib_ui();
		this.update_sel_count();
		$('#vp-section-visor').removeClass('hidden');
		$('#vp-section-confirmar').removeClass('hidden');
		this.update_create_button();
	}

	// ------------------------------------------------------------------
	// Paso 4 — preset por figura (override puntual sobre el global)
	// ------------------------------------------------------------------

	// Matching client-side por bbox-center (Punto, MSG_033) — sin llamada al
	// backend, ya tenemos this.presets completo desde vectorize_image.
	find_entity_in_preset(sourceEntityId, sourcePresetName, targetPresetName) {
		const srcPreset = this.presets.find((p) => p.name === sourcePresetName);
		const srcEntity = srcPreset && (srcPreset.entities || []).find((e) => e.id === sourceEntityId);
		if (!srcEntity || !srcEntity.bbox_approx) return null;

		const bb = srcEntity.bbox_approx;
		const refCx = bb.x + bb.w / 2;
		const refCy = bb.y + bb.h / 2;
		const tol = Math.max(Math.max(bb.w, bb.h) * 0.10, 5);

		const targetPreset = this.presets.find((p) => p.name === targetPresetName);
		const targetEntities = (targetPreset && targetPreset.entities) || [];
		let best = null;
		let bestDist = Infinity;
		targetEntities.forEach((e) => {
			if (!e.bbox_approx) return;
			const ebb = e.bbox_approx;
			const cx = ebb.x + ebb.w / 2;
			const cy = ebb.y + ebb.h / 2;
			const dist = Math.hypot(cx - refCx, cy - refCy);
			if (dist < bestDist) {
				bestDist = dist;
				best = e;
			}
		});
		return best && bestDist <= tol ? best : null;
	}

	// SVG del preset ya parseado (cacheado) — para extraer un <path id="eN">
	// puntual sin reparsear svg_full en cada miniatura.
	get_parsed_preset_svg(preset) {
		if (!this._presetSvgCache[preset.name]) {
			const div = document.createElement('div');
			div.innerHTML = preset.svg_full || '';
			this._presetSvgCache[preset.name] = div.querySelector('svg');
		}
		return this._presetSvgCache[preset.name];
	}

	// Miniatura de UNA figura puntual — recorta al bbox_approx de esa entidad
	// (mismo espacio de coordenadas que el d del path, antes del <g transform>
	// translate/scale de potrace: no lo replicamos porque para comparar calidad
	// de trazo entre presets no hace falta que coincida la orientación con el
	// visor principal — puede verse espejado/rotado respecto a este, es un
	// costo cosmético aceptado, no un bug).
	entity_thumb_svg(preset, entityId) {
		const entityMeta = (preset.entities || []).find((e) => e.id === entityId);
		if (!entityMeta || !entityMeta.bbox_approx) return '';
		const parsedSvg = this.get_parsed_preset_svg(preset);
		const pathEl = parsedSvg && parsedSvg.querySelector('#' + CSS.escape(entityId));
		if (!pathEl) return '';
		const bb = entityMeta.bbox_approx;
		const pad = Math.max(bb.w, bb.h, 1) * 0.15;
		const vb = (bb.x - pad) + ' ' + (bb.y - pad) + ' ' + (bb.w + pad * 2) + ' ' + (bb.h + pad * 2);
		return '<svg viewBox="' + vb + '" xmlns="http://www.w3.org/2000/svg">' + pathEl.outerHTML + '</svg>';
	}

	// Preset+entity_id efectivamente asignado a una figura seleccionada —
	// el override si el usuario lo cambió, si no el global del paso 2.
	get_entity_assignment(sourceEntityId) {
		const override = this.entityOverrides[sourceEntityId];
		if (override) return override;
		return { preset: this.presets[this.preset_idx].name, entity_id: sourceEntityId };
	}

	render_figuras_grid() {
		const ids = this.get_selected_ids();
		const $grid = $('#vp-figuras-grid').empty();
		if (!ids.length) {
			$('#vp-section-figuras').addClass('hidden');
			return;
		}
		$('#vp-section-figuras').removeClass('hidden');

		ids.forEach((sourceId) => {
			const isCustom = !!this.entityOverrides[sourceId];
			const assignment = this.get_entity_assignment(sourceId);
			const presetObj = this.presets.find((p) => p.name === assignment.preset);
			const thumb = presetObj ? this.entity_thumb_svg(presetObj, assignment.entity_id) : '';

			const card = $(
				'<div class="vp-figura-card' + (isCustom ? ' vp-custom' : '') + '">' +
					'<div class="vp-figura-thumb">' + thumb + '</div>' +
					'<div class="vp-figura-preset">' + frappe.utils.escape_html(assignment.preset) + '</div>' +
					'<button type="button" class="vp-figura-cambiar">' + __('Cambiar') + '</button>' +
					'</div>'
			);
			card.find('.vp-figura-cambiar').on('click', () => this.open_entity_preset_picker(sourceId));
			$grid.append(card);
		});
	}

	// Debounce: con selecciones grandes (recuadro sobre una retícula de
	// decenas/cientos de figuras) no queremos re-renderizar la grilla completa
	// en cada tick del arrastre — solo cuando la selección se asienta.
	schedule_figuras_render() {
		clearTimeout(this._figurasRenderTimer);
		this._figurasRenderTimer = setTimeout(() => this.render_figuras_grid(), 250);
	}

	open_entity_preset_picker(sourceId) {
		const sourcePresetName = this.presets[this.preset_idx].name;
		const currentAssignment = this.get_entity_assignment(sourceId);

		const cardsHtml = this.presets.map((p) => {
			const match = this.find_entity_in_preset(sourceId, sourcePresetName, p.name);
			const isSelected = p.name === currentAssignment.preset;
			if (!match) {
				return (
					'<div class="vp-variant-card disabled" data-preset="' + frappe.utils.escape_html(p.name) + '">' +
						'<div class="vp-variant-thumb"><span class="vp-variant-na">' + __('no disponible') + '</span></div>' +
						'<div class="vp-variant-name">' + frappe.utils.escape_html(p.name) + '</div>' +
						'</div>'
				);
			}
			const thumb = this.entity_thumb_svg(p, match.id);
			return (
				'<div class="vp-variant-card' + (isSelected ? ' selected' : '') + '" data-preset="' +
					frappe.utils.escape_html(p.name) + '" data-entity="' + frappe.utils.escape_html(match.id) + '">' +
					'<div class="vp-variant-thumb">' + thumb + '</div>' +
					'<div class="vp-variant-name">' + frappe.utils.escape_html(p.name) + '</div>' +
					'</div>'
			);
		}).join('');

		const d = new frappe.ui.Dialog({
			title: __('Elegir preset para esta figura'),
			fields: [{ fieldtype: 'HTML', fieldname: 'variants_html', options: '<div class="vp-variant-grid">' + cardsHtml + '</div>' }],
		});

		d.$wrapper.find('.vp-variant-card:not(.disabled)').on('click', (e) => {
			const $card = $(e.currentTarget);
			const presetName = $card.data('preset');
			const entityId = $card.data('entity');
			if (presetName === sourcePresetName && entityId === sourceId) {
				// Volver al global — sin override.
				delete this.entityOverrides[sourceId];
			} else {
				this.entityOverrides[sourceId] = { preset: presetName, entity_id: entityId };
			}
			d.hide();
			this.render_figuras_grid();
		});

		d.show();
	}

	// ------------------------------------------------------------------
	// Visor — modo, zoom, pan, selección (clic + recuadro), calibración
	// ------------------------------------------------------------------

	set_mode(mode) {
		this.mode = mode;
		this.calibArm = null;
		$('.vp-tool').removeClass('active');
		$('#vp-tool-' + mode).addClass('active');
		$('#vp-viewer').toggleClass('mode-pan', mode === 'pan');
		$('#vp-viewer').toggleClass('mode-select', mode === 'select');
		$('#vp-calib-panel').toggleClass('hidden', mode !== 'calibrate');

		const hints = {
			select: __('Modo Seleccionar: clic en una entidad para incluirla/excluirla. Arrastrá sobre el fondo para seleccionar varias (recuadro).'),
			calibrate: __('Modo Calibrar: elegí qué línea dibujar y arrastrá sobre el visor. Después ingresá la medida real de la vertical.'),
			pan: __('Modo Mover vista: arrastrá para desplazarte por la imagen. Usá la rueda del mouse para zoom en cualquier modo.'),
		};
		$('#vp-mode-hint').text(hints[mode] || '');
		this.update_calib_buttons();
	}

	apply_viewbox() {
		if (!this.svgEl || !this.viewBox) return;
		const v = this.viewBox;
		this.svgEl.setAttribute('viewBox', `${v.x} ${v.y} ${v.w} ${v.h}`);
	}

	reset_view() {
		if (!this.origViewBox) return;
		this.viewBox = Object.assign({}, this.origViewBox);
		this.apply_viewbox();
	}

	zoom_by(factor) {
		if (!this.viewBox) return;
		const container = document.getElementById('vp-viewer');
		const rect = container.getBoundingClientRect();
		this._zoom_at(rect.left + rect.width / 2, rect.top + rect.height / 2, factor);
	}

	_zoom_at(clientX, clientY, factor) {
		const v = this.viewBox;
		// Punto SVG bajo el cursor (correcto con letterboxing, ver client_to_view).
		const p = this.client_to_view(clientX, clientY);
		// Su fracción DENTRO del viewBox actual — esto es pura geometría de
		// viewBox, no depende de la pantalla, así que no hay bug de letterboxing acá.
		const fx = (p.x - v.x) / v.w;
		const fy = (p.y - v.y) / v.h;
		let newW = v.w * factor;
		let newH = v.h * factor;
		// límites: no alejar más que 4x el original, no acercar más de 40x
		const maxW = this.origViewBox.w * 4;
		const minW = this.origViewBox.w / 40;
		newW = Math.min(maxW, Math.max(minW, newW));
		newH = Math.min(maxW * (this.origViewBox.h / this.origViewBox.w), Math.max(minW * (this.origViewBox.h / this.origViewBox.w), newH));
		this.viewBox = {
			x: p.x - fx * newW,
			y: p.y - fy * newH,
			w: newW,
			h: newH,
		};
		this.apply_viewbox();
	}

	// Convierte coordenadas de pantalla (clientX/Y) a unidades del viewBox
	// (= "SVG display units", las mismas que espera escala_display del backend).
	//
	// getScreenCTM() (matriz real pantalla->SVG) en vez de calcular a mano con
	// getBoundingClientRect() del contenedor: el <svg> no tiene
	// preserveAspectRatio="none", así que con el default (xMidYMid meet) el
	// navegador agrega letterboxing/pillarboxing cuando la proporción del
	// viewBox no coincide con la del contenedor (520px fijo) — la cuenta a
	// mano asumía que el SVG llena el rect completo sin franjas, y el clic
	// quedaba corrido (bug reportado por Constantino, MSG_032 de Nova).
	// getScreenCTM() contempla el letterboxing automáticamente.
	client_to_view(clientX, clientY, ctm) {
		const pt = this.svgEl.createSVGPoint();
		pt.x = clientX;
		pt.y = clientY;
		const screenCTM = ctm || this.svgEl.getScreenCTM();
		const svgPt = pt.matrixTransform(screenCTM.inverse());
		return { x: svgPt.x, y: svgPt.y };
	}

	wire_viewer_events() {
		const container = document.getElementById('vp-viewer');
		// Limpiar listeners previos clonando el nodo no es viable (perdería el svg);
		// en su lugar, usamos flags de instancia + un solo listener persistente por
		// evento, seguro porque wire_viewer_events se llama una vez por selección de
		// preset y el container es el mismo elemento del DOM durante toda la page.
		if (this._wired) return;
		this._wired = true;

		container.addEventListener('wheel', (e) => {
			e.preventDefault();
			const factor = e.deltaY > 0 ? 1.15 : 0.87;
			this._zoom_at(e.clientX, e.clientY, factor);
		}, { passive: false });

		container.addEventListener('click', (e) => {
			if (this.mode !== 'select') return;
			const path = e.target.closest('path');
			if (!path) return;
			path.classList.toggle('vp-selected');
			this.update_sel_count();
		});

		container.addEventListener('pointerdown', (e) => this.on_pointer_down(e));
		container.addEventListener('pointermove', (e) => this.on_pointer_move(e));
		container.addEventListener('pointerup', (e) => this.on_pointer_up(e));
		container.addEventListener('pointercancel', () => { this._drag = null; this.clear_rubber_box(); });
	}

	on_pointer_down(e) {
		const container = document.getElementById('vp-viewer');
		const isPath = !!e.target.closest('path');

		if (this.mode === 'pan') {
			container.setPointerCapture(e.pointerId);
			container.classList.add('panning');
			// CTM congelada al empezar el arrastre: el pan va actualizando
			// this.viewBox (y por lo tanto la CTM real del <svg>) en cada
			// pointermove, así que recalcular getScreenCTM() en el medio del
			// gesto compararía puntos en dos sistemas de referencia distintos.
			// Con la CTM fija, start/current quedan en el mismo sistema.
			this._drag = {
				type: 'pan',
				startClientX: e.clientX, startClientY: e.clientY,
				startView: Object.assign({}, this.viewBox),
				startCTM: this.svgEl.getScreenCTM(),
			};
			return;
		}
		if (this.mode === 'calibrate' && this.calibArm) {
			container.setPointerCapture(e.pointerId);
			const p = this.client_to_view(e.clientX, e.clientY);
			this._drag = { type: 'calib', line: this.calibArm, start: p };
			return;
		}
		if (this.mode === 'select' && !isPath) {
			container.setPointerCapture(e.pointerId);
			const rect = container.getBoundingClientRect();
			this._drag = {
				type: 'rubber',
				startClientX: e.clientX, startClientY: e.clientY,
				containerRect: rect,
			};
		}
	}

	on_pointer_move(e) {
		if (!this._drag) return;
		if (this._drag.type === 'pan') {
			const v0 = this._drag.startView;
			// Mismo principio que client_to_view (CTM en vez de rect a mano),
			// pero con la CTM congelada en pointerdown para no comparar contra
			// un sistema de referencia que se mueve durante el propio gesto.
			const startSvg = this.client_to_view(this._drag.startClientX, this._drag.startClientY, this._drag.startCTM);
			const curSvg = this.client_to_view(e.clientX, e.clientY, this._drag.startCTM);
			const dx = curSvg.x - startSvg.x;
			const dy = curSvg.y - startSvg.y;
			this.viewBox = { x: v0.x - dx, y: v0.y - dy, w: v0.w, h: v0.h };
			this.apply_viewbox();
		} else if (this._drag.type === 'calib') {
			this.draw_calib_preview(this._drag.start, this.client_to_view(e.clientX, e.clientY), this._drag.line);
		} else if (this._drag.type === 'rubber') {
			this.draw_rubber_box(this._drag.startClientX, this._drag.startClientY, e.clientX, e.clientY);
		}
	}

	on_pointer_up(e) {
		const container = document.getElementById('vp-viewer');
		container.classList.remove('panning');
		if (!this._drag) return;

		if (this._drag.type === 'calib') {
			const end = this.client_to_view(e.clientX, e.clientY);
			this.commit_calib_line(this._drag.line, this._drag.start, end);
		} else if (this._drag.type === 'rubber') {
			this.finish_rubber_select(this._drag.startClientX, this._drag.startClientY, e.clientX, e.clientY);
		}
		this._drag = null;
	}

	// ---- Selección por recuadro (rubber-band, en coordenadas de PANTALLA) ----

	draw_rubber_box(x1, y1, x2, y2) {
		let box = document.getElementById('vp-rubber-box-el');
		const container = document.getElementById('vp-viewer');
		if (!box) {
			box = document.createElement('div');
			box.id = 'vp-rubber-box-el';
			box.className = 'vp-rubber-box';
			container.appendChild(box);
		}
		const rect = container.getBoundingClientRect();
		const left = Math.min(x1, x2) - rect.left;
		const top = Math.min(y1, y2) - rect.top;
		box.style.left = left + 'px';
		box.style.top = top + 'px';
		box.style.width = Math.abs(x2 - x1) + 'px';
		box.style.height = Math.abs(y2 - y1) + 'px';
	}

	clear_rubber_box() {
		const box = document.getElementById('vp-rubber-box-el');
		if (box) box.remove();
	}

	finish_rubber_select(x1, y1, x2, y2) {
		this.clear_rubber_box();
		// Umbral mínimo: un clic sin arrastre real no selecciona nada (evita
		// deseleccionar por error con un clic-suelto sobre el fondo).
		if (Math.abs(x2 - x1) < 4 && Math.abs(y2 - y1) < 4) return;
		const rx1 = Math.min(x1, x2), rx2 = Math.max(x1, x2);
		const ry1 = Math.min(y1, y2), ry2 = Math.max(y1, y2);
		const paths = this.svgEl.querySelectorAll('path');
		paths.forEach((p) => {
			const b = p.getBoundingClientRect();
			const intersects = b.left < rx2 && b.right > rx1 && b.top < ry2 && b.bottom > ry1;
			if (intersects) p.classList.add('vp-selected');
		});
		this.update_sel_count();
	}

	select_all(on) {
		if (!this.svgEl) return;
		this.svgEl.querySelectorAll('path').forEach((p) => p.classList.toggle('vp-selected', on));
		this.update_sel_count();
	}

	update_sel_count() {
		const n = this.svgEl ? this.svgEl.querySelectorAll('path.vp-selected').length : 0;
		$('#vp-sel-count').text(n + ' ' + __('entidades seleccionadas'));
		this.update_create_button();
		this.schedule_figuras_render();
	}

	get_selected_ids() {
		if (!this.svgEl) return [];
		return [...this.svgEl.querySelectorAll('path.vp-selected')].map((p) => p.id).filter(Boolean);
	}

	// ---- Calibración: dos líneas + una medida ----

	arm_calib_line(which) {
		this.calibArm = which;
		this.update_calib_buttons();
	}

	update_calib_buttons() {
		$('#vp-calib-btn-v').toggleClass('done', !!this.calib.vLine);
		$('#vp-calib-btn-h').toggleClass('done', !!this.calib.hLine);
	}

	draw_calib_preview(start, end, which) {
		let line = document.getElementById('vp-calib-preview-' + which);
		if (!line) {
			line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
			line.id = 'vp-calib-preview-' + which;
			line.setAttribute('class', 'vp-calib-line' + (which === 'v' ? ' vertical' : ''));
			this.svgEl.appendChild(line);
		}
		line.setAttribute('x1', start.x); line.setAttribute('y1', start.y);
		line.setAttribute('x2', end.x); line.setAttribute('y2', end.y);
	}

	commit_calib_line(which, start, end) {
		const dx = end.x - start.x, dy = end.y - start.y;
		const len = Math.sqrt(dx * dx + dy * dy);
		if (len < 1e-6) return; // línea de largo cero — ignorar
		this.calib[which === 'v' ? 'vLine' : 'hLine'] = { start, end, len };
		this.calibArm = null;
		this.update_calib_buttons();
		this.update_calib_ui();
	}

	update_calib_ui() {
		const both = !!(this.calib.vLine && this.calib.hLine);
		$('#vp-calib-measure').toggleClass('hidden', !both);
		const parts = [];
		if (this.calib.vLine) parts.push(__('vertical dibujada'));
		if (this.calib.hLine) parts.push(__('horizontal dibujada'));
		if (this.calib.escala_display) parts.push(__('calibrado ✓'));
		$('#vp-calib-lines-status').text(parts.join(' · '));
		$('#vp-calib-status').text(
			this.calib.escala_display
				? __('Calibración: escala {0} mm/unidad', [this.calib.escala_display.toFixed(4)])
				: __('Calibración: sin definir')
		);
	}

	apply_calibration() {
		const vMm = parseFloat($('#vp-calib-vmm').val());
		if (!(vMm > 0)) {
			frappe.show_alert({ message: __('Ingresá la medida real de la línea vertical (mm).'), indicator: 'red' });
			return;
		}
		if (!this.calib.vLine || !this.calib.hLine) return;
		const escala = vMm / this.calib.vLine.len;
		const step_y = vMm;
		const step_x = this.calib.hLine.len * escala;
		this.calib.vMm = vMm;
		this.calib.escala_display = escala;
		this.calib.step_x_mm = step_x;
		this.calib.step_y_mm = step_y;
		$('#vp-stepx').val(step_x.toFixed(2));
		$('#vp-stepy').val(step_y.toFixed(2));
		this.update_calib_ui();
		this.update_create_button();
		frappe.show_alert({ message: __('Calibración aplicada'), indicator: 'green' });
	}

	update_create_button() {
		const ready = this.get_selected_ids().length > 0 && !!this.calib.escala_display;
		$('#vp-btn-crear').prop('disabled', !ready);
	}

	// ------------------------------------------------------------------
	// Paso 4 — crear patrón
	// ------------------------------------------------------------------

	crear() {
		const status = $('#vp-confirm-status').css('color', '').text('');
		const fail = (msg) => status.css('color', 'var(--si-red)').text(msg);

		if (!this.run_id) return fail(__('La corrida expiró. Volvé a vectorizar la imagen.'));
		if (this.preset_idx == null) return fail(__('Elegí un preset.'));
		const selected_entity_ids = this.get_selected_ids();
		if (!selected_entity_ids.length) return fail(__('Seleccioná al menos una entidad del tile.'));
		if (!this.calib.escala_display) return fail(__('Calibrá la escala antes de crear el patrón.'));

		const nombre = $('#vp-nombre').val().trim();
		const visibilidad = $('#vp-visibilidad').val();
		const customer = this.get_customer();
		if (!nombre) return fail(__('Falta el nombre.'));
		if (visibilidad === 'Exclusivo' && !customer)
			return fail(__('Elegí el cliente para un patrón exclusivo.'));

		status.text(__('Creando patrón…'));
		const btn = $('#vp-btn-crear').prop('disabled', true);

		// selected_items en vez de preset + selected_entity_ids (contrato nuevo,
		// MSG_033 de Punto): cada figura lleva su propio preset asignado —
		// el override del paso 4 si el usuario lo cambió, si no el global.
		const selected_items = selected_entity_ids.map((id) => this.get_entity_assignment(id));

		frappe.call({
			method: 'sistema_industrial.api.vectorizer.compose_pattern',
			args: {
				run_id: this.run_id,
				selected_items: selected_items,
				escala_display: this.calib.escala_display,
				step_x_mm: this.calib.step_x_mm,
				step_y_mm: this.calib.step_y_mm,
				nombre: nombre,
				visibilidad: visibilidad === 'Publico' ? 'Público' : 'Exclusivo',
				customer: visibilidad === 'Exclusivo' ? customer : null,
				descripcion: __('Vectorizado de imagen'),
			},
			callback: (r) => {
				const m = r.message || {};
				if (m.ok) {
					status.css('color', 'var(--si-green)')
						.text(__('✓ Patrón creado: ') + m.name + ' (v' + (m.version || 1) + ')');
					frappe.show_alert({
						message: __('Patrón "{0}" creado — ya aparece en la galería del panel', [m.name]),
						indicator: 'green',
					});
				} else {
					fail(__('Error: ') + (m.error || __('desconocido')));
				}
			},
			error: () => fail(__('Error al crear el patrón. Revisá la consola.')),
			always: () => this.update_create_button(),
		});
	}
}
