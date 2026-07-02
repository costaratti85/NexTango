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
		this.file_url = null;       // imagen subida (FileUploader)
		this.file_label = null;
		this.run_id = null;         // efímero — solo en memoria (Punto: se pierde al navegar)
		this.figuras = [];          // r.message.figuras
		this.preset_names = [];
		this.selecciones = {};      // figura_id -> preset | null(descartada/sin elegir)

		this.make_customer_control();
		this.bind_events();
	}

	make_customer_control() {
		this.customer_control = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Link',
				options: 'Customer',
				fieldname: 'cliente',
				placeholder: __('Cliente'),
			},
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
	}

	// ------------------------------------------------------------------
	// Paso 1 — subir imagen
	// ------------------------------------------------------------------

	pick_image() {
		new frappe.ui.FileUploader({
			as_dataurl: false,
			allow_multiple: false,
			restrictions: { allowed_file_types: ['image/*', '.png', '.jpg', '.jpeg'] },
			make_attachments_public: false,
			on_success: (file_doc) => {
				this.file_url = file_doc.file_url;
				this.file_label = file_doc.file_name || file_doc.file_url;
				$('#vp-drop-prompt').addClass('hidden');
				$('#vp-file-name').removeClass('hidden').text('✓ ' + this.file_label);
				$('#vp-drop').addClass('has-file');
				$('#vp-btn-vectorizar').prop('disabled', false);
			},
		});
	}

	// ------------------------------------------------------------------
	// Paso 1 → 2 — vectorizar
	// ------------------------------------------------------------------

	vectorizar() {
		if (!this.file_url) return;
		const status = $('#vp-status').css('color', '').text('');
		$('#vp-spinner').removeClass('hidden');
		$('#vp-btn-vectorizar').prop('disabled', true);
		// Ocultar resultados previos si re-vectoriza
		$('#vp-section-figuras').addClass('hidden');
		$('#vp-section-confirmar').addClass('hidden');

		frappe.call({
			method: 'sistema_industrial.api.vectorizer.vectorize_image',
			args: { file_url: this.file_url, presets: null },
			callback: (r) => {
				const m = r.message || {};
				this.run_id = m.run_id || null;
				this.preset_names = m.preset_names || [];
				this.figuras = m.figuras || [];
				if (!this.run_id || !this.figuras.length) {
					status.css('color', 'var(--si-red)')
						.text(__('No se detectaron figuras en la imagen. Probá con una imagen de más contraste.'));
					return;
				}
				// Pre-selección: para cada figura, la primera variante detectada.
				this.selecciones = {};
				this.figuras.forEach((f) => {
					const first = (f.variantes || []).find((v) => v && v.svg_preview);
					this.selecciones[f.figura_id] = first ? first.preset : null;
				});
				this.render_figuras();
				$('#vp-section-figuras').removeClass('hidden');
				$('#vp-section-confirmar').removeClass('hidden');
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
	// Paso 2 — grilla de figuras × variantes
	// ------------------------------------------------------------------

	render_figuras() {
		const cont = $('#vp-figuras').empty();

		this.figuras.forEach((f, idx) => {
			const descartada = this.selecciones[f.figura_id] == null;
			const figEl = $('<div class="vp-fig">').toggleClass('descartada', descartada);

			// Cabecera: título + bbox + descartar/restaurar
			const head = $('<div class="vp-fig-head">');
			const left = $('<div>');
			left.append($('<span class="vp-fig-title">').text(__('Figura {0}', [idx + 1])));
			if (f.bbox) {
				const b = f.bbox;
				left.append(
					$('<span class="vp-fig-bbox" style="margin-left:10px">').text(
						Math.round(b.w) + '×' + Math.round(b.h) + ' mm'
					)
				);
			}
			head.append(left);
			const toggle = $('<button class="btn btn-xs btn-default">')
				.text(descartada ? __('Incluir') : __('Descartar'))
				.on('click', () => this.toggle_descartar(f.figura_id));
			head.append(toggle);
			figEl.append(head);

			// Variantes: una celda por preset
			const vars = $('<div class="vp-variants">');
			(f.variantes || []).forEach((v) => {
				if (!v) return;
				const cell = $('<div class="vp-var">').attr('data-preset', v.preset);
				const sel = this.selecciones[f.figura_id] === v.preset;

				if (v.svg_preview) {
					const svgWrap = $('<div class="vp-var-svg">');
					// svg_preview es un <svg> completo — inyección directa (no va al template).
					svgWrap.html(v.svg_preview);
					cell.append(svgWrap);
					cell.append($('<div class="vp-var-name">').text(v.preset));
					if (v.metrics && v.metrics.nodes != null) {
						cell.append($('<div class="vp-var-metrics">').text(v.metrics.nodes + ' ' + __('nodos')));
					}
					cell.toggleClass('selected', sel);
					cell.on('click', () => this.select_variante(f.figura_id, v.preset));
				} else {
					// Preset que no detectó esta figura
					cell.addClass('no-det');
					cell.append($('<div class="vp-var-nodet">').text(__('no detectada')));
					cell.append($('<div class="vp-var-name">').text(v.preset));
				}
				vars.append(cell);
			});
			figEl.append(vars);
			cont.append(figEl);
		});

		this.update_sel_count();
	}

	select_variante(figura_id, preset) {
		this.selecciones[figura_id] = preset;   // elegir también re-incluye una descartada
		this.render_figuras();
	}

	toggle_descartar(figura_id) {
		if (this.selecciones[figura_id] == null) {
			// Restaurar: primera variante detectada
			const f = this.figuras.find((x) => x.figura_id === figura_id);
			const first = f && (f.variantes || []).find((v) => v && v.svg_preview);
			this.selecciones[figura_id] = first ? first.preset : null;
		} else {
			this.selecciones[figura_id] = null;   // descartar
		}
		this.render_figuras();
	}

	update_sel_count() {
		const n = this.get_selecciones().length;
		const total = this.figuras.length;
		$('#vp-sel-count').text(
			__('{0} de {1} figuras seleccionadas para el patrón', [n, total])
		);
		$('#vp-btn-crear').prop('disabled', n === 0);
	}

	get_selecciones() {
		return this.figuras
			.filter((f) => this.selecciones[f.figura_id] != null)
			.map((f) => ({ figura_id: f.figura_id, preset: this.selecciones[f.figura_id] }));
	}

	// ------------------------------------------------------------------
	// Paso 3 — crear patrón
	// ------------------------------------------------------------------

	crear() {
		const status = $('#vp-confirm-status').css('color', '').text('');
		const fail = (msg) => status.css('color', 'var(--si-red)').text(msg);

		const selecciones = this.get_selecciones();
		if (!this.run_id) return fail(__('La corrida expiró. Volvé a vectorizar la imagen.'));
		if (!selecciones.length) return fail(__('Elegí al menos una figura.'));

		const nombre = $('#vp-nombre').val().trim();
		const stepx = parseFloat($('#vp-stepx').val());
		const stepy = parseFloat($('#vp-stepy').val());
		const visibilidad = $('#vp-visibilidad').val();
		const customer = this.get_customer();

		if (!nombre) return fail(__('Falta el nombre.'));
		if (!(stepx > 0)) return fail(__('Paso X inválido.'));
		if (!(stepy > 0)) return fail(__('Paso Y inválido.'));
		if (visibilidad === 'Exclusivo' && !customer)
			return fail(__('Elegí el cliente para un patrón exclusivo.'));

		status.css('color', '').text(__('Creando patrón…'));
		const btn = $('#vp-btn-crear').prop('disabled', true);

		frappe.call({
			method: 'sistema_industrial.api.vectorizer.compose_pattern',
			args: {
				run_id: this.run_id,
				selecciones: selecciones,
				nombre: nombre,
				step_x: stepx,
				step_y: stepy,
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
			always: () => btn.prop('disabled', false),
		});
	}
}
