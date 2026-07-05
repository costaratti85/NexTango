frappe.pages['panel-decorativo'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Panel Decorativo',
		single_column: true,
	});

	$(frappe.render_template('panel_decorativo', {})).appendTo(page.body);
	new PanelDecorativo(page);
};

class PanelDecorativo {
	constructor(page) {
		this.page = page;
		this.batches = [];
		this.lineas = [];        // resultado de calcular() con factores agregados
		this.materials = [];     // rows de api.materiales.get_all
		this.matIndex = {};      // {material: [{espesor_mm, precio_por_kg, precio_plegar_por_kg, ...}]}
		this.precios = { precio_segundo_laser: 0, precio_por_plegado: 0 };
		this.patterns = [];              // rows de api.patrones.get_all
		this.selected_patron = 'tresbolillo';
		this.dist_mode = 'centradas';

		this.make_customer_control();
		this.render_pattern_gallery();
		this.bind_events();
		this.load_initial_data();
	}

	// ------------------------------------------------------------------
	// Galería de patrones — nativos (SVG inline) + DXF (thumbnails PNG)
	// ------------------------------------------------------------------

	static get NATIVE_PATTERNS() {
		const circ = (cx, cy) => `<circle cx="${cx}" cy="${cy}" r="6" fill="none" stroke="#176b87" stroke-width="1.5"/>`;
		const sq = (x, y) => `<rect x="${x}" y="${y}" width="11" height="11" fill="none" stroke="#176b87" stroke-width="1.5"/>`;
		let tres = '', cuadC = '', cuadS = '';
		for (let r = 0; r < 4; r++)
			for (let c = 0; c < 6; c++) {
				const offs = r % 2 ? 10 : 0;
				tres += circ(14 + c * 20 + offs, 13 + r * 21);
				cuadC += circ(14 + c * 20, 13 + r * 21);
				cuadS += sq(8 + c * 20, 7 + r * 21);
			}
		const wrap = (inner) => `<svg class="pd-pat-thumb-svg" viewBox="0 0 130 90" xmlns="http://www.w3.org/2000/svg">${inner}</svg>`;
		return [
			{ val: 'tresbolillo', label: __('Tresbolillo'), svg: wrap(tres) },
			{ val: 'cuadriculado_circle', label: __('Cuadriculado redondo'), svg: wrap(cuadC) },
			{ val: 'cuadriculado_square', label: __('Cuadriculado cuadrado'), svg: wrap(cuadS) },
		];
	}

	// SVG genérico de fallback para patrones DXF sin thumbnail_url.
	static get FALLBACK_THUMB_SVG() {
		return '<svg class="pd-pat-thumb-svg" viewBox="0 0 130 90" xmlns="http://www.w3.org/2000/svg">'
			+ '<rect x="10" y="10" width="110" height="70" fill="none" stroke="#176b87" stroke-width="2"/></svg>';
	}

	render_pattern_gallery() {
		const gal = $('#pd-patron-gallery').empty();

		PanelDecorativo.NATIVE_PATTERNS.forEach((p) => {
			const card = $('<div class="pd-pat-card">').attr('data-val', p.val);
			card.append(p.svg);
			card.append($('<div class="pd-pat-name">').text(p.label));
			card.on('click', () => this.select_patron(p.val));
			gal.append(card);
		});

		this.patterns.forEach((p, i) => {
			const val = 'dxf:' + i;
			const available = !!p.file_available;
			const card = $('<div class="pd-pat-card">')
				.attr('data-val', val)
				.toggleClass('disabled', !available);
			if (p.thumbnail_url) {
				card.append(
					$('<img class="pd-pat-thumb" loading="lazy">')
						.attr('src', p.thumbnail_url)
						.attr('alt', p.label || p.name)
				);
			} else {
				card.append($(PanelDecorativo.FALLBACK_THUMB_SVG));
			}
			card.append($('<div class="pd-pat-name">').text(p.label || p.name));
			if (!available) card.append($('<span class="pd-pat-badge">').text(__('No disponible')));
			if (available) card.on('click', () => this.select_patron(val));
			gal.append(card);
		});

		this.update_gallery_selection();
	}

	update_gallery_selection() {
		$('#pd-patron-gallery .pd-pat-card').removeClass('selected');
		$('#pd-patron-gallery .pd-pat-card[data-val="' + this.selected_patron + '"]').addClass('selected');
	}

	select_patron(val) {
		this.selected_patron = val;
		this.update_gallery_selection();
		$('#pd-params-tresbolillo').toggleClass('hidden', val !== 'tresbolillo');
		$('#pd-params-cuadriculado').toggleClass(
			'hidden',
			val !== 'cuadriculado_circle' && val !== 'cuadriculado_square'
		);
		// El paso X/Y de un patrón DXF/vectorizado es una propiedad DEL PATRÓN
		// (se fija al cargarlo/calibrarlo) — no se reingresa acá. add_batch lo
		// toma directo de dxf_row.step_x/step_y.
	}

	// ------------------------------------------------------------------
	// Cliente — Link a Customer con autocompletado
	// ------------------------------------------------------------------

	make_customer_control() {
		this.customer_control = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Link',
				options: 'Customer',
				fieldname: 'customer',
				placeholder: __('Nombre o código de cliente'),
				onchange: () => this.on_customer_change(),
			},
			parent: $('#pd-customer-field'),
			render_input: true,
		});
		sistema_industrial.attach_customer_sync_button(this.customer_control, '#pd-customer-field');
	}

	get_customer() {
		return (this.customer_control && this.customer_control.get_value()) || '';
	}

	// Descuento default del cliente (si_tango_discount, sincronizado desde Tango)
	// pre-cargado al elegir cliente. Queda editable — es un default, no un candado.
	on_customer_change() {
		const customer = this.get_customer();
		if (!customer) return;
		frappe.db.get_value('Customer', customer, 'si_tango_discount').then((r) => {
			const v = parseFloat(r.message && r.message.si_tango_discount);
			$('#pd-descuento').val(isNaN(v) ? 0 : v);
			this.refresh_costos();
		});
	}

	// ------------------------------------------------------------------
	// Carga inicial
	// ------------------------------------------------------------------

	load_initial_data() {
		frappe.call({
			method: 'sistema_industrial.api.materiales.get_all',
			callback: (r) => {
				const msg = r.message || {};
				this.materials = (msg.rows || []).filter((m) => m.activo);
				this.build_material_index();
				this.populate_material_select();
				if (msg.source === 'legacy_json') {
					frappe.show_alert({
						message: __('Materiales desde JSON legacy (migración pendiente)'),
						indicator: 'orange',
					});
				}
			},
			error: () => {
				$('#pd-material').html('<option value="">Error al cargar materiales</option>');
			},
		});

		frappe.call({
			method: 'sistema_industrial.api.materiales.get_precios',
			callback: (r) => {
				if (r.message) this.precios = r.message;
			},
		});

		this.load_patterns();
	}

	// ------------------------------------------------------------------
	// Patrones DXF custom — degradación silenciosa si el endpoint no existe
	// ------------------------------------------------------------------
	// Contrato asumido (a confirmar con Punto):
	//   sistema_industrial.api.patrones.get_all
	//   r.message = { rows: [{ name, file_path, ... }] }
	// Se usa fetch directo (no frappe.call) para que un 404 pre-endpoint
	// no dispare el diálogo de error de Frappe en cada carga de página.

	load_patterns() {
		fetch('/api/method/sistema_industrial.api.patrones.get_all', {
			headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
		})
			.then((r) => (r.ok ? r.json() : null))
			.then((d) => {
				const rows = (d && d.message && d.message.rows) || [];
				if (!rows.length) return;
				this.patterns = rows;
				this.render_pattern_gallery();
			})
			.catch(() => {}); // sin endpoint — la galería queda con los modos nativos
	}

	build_material_index() {
		this.matIndex = {};
		this.materials.forEach((m) => {
			if (!this.matIndex[m.material]) this.matIndex[m.material] = [];
			this.matIndex[m.material].push(m);
		});
		Object.values(this.matIndex).forEach((list) =>
			list.sort((a, b) => a.espesor_mm - b.espesor_mm)
		);
	}

	populate_material_select() {
		const sel = $('#pd-material');
		sel.empty().append('<option value="">— elegir —</option>');
		Object.keys(this.matIndex)
			.sort()
			.forEach((name) => sel.append($('<option>').val(name).text(name)));
	}

	// Devuelve la row de material para (material, espesor) — para precios por kg
	material_row(material, espesor_mm) {
		const list = this.matIndex[material] || [];
		return (
			list.find((m) => Math.abs(m.espesor_mm - espesor_mm) < 0.001) || null
		);
	}

	// ------------------------------------------------------------------
	// Eventos
	// ------------------------------------------------------------------

	bind_events() {
		$('#pd-material').on('change', () => this.on_material_change());
		$('#pd-dist-centradas').on('click', () => this.set_dist_mode('centradas'));
		$('#pd-dist-cortar').on('click', () => this.set_dist_mode('cortar'));
		$('#pd-btn-add').on('click', () => this.add_batch());
		$('#pd-btn-calcular').on('click', () => this.calcular());
		$('#pd-btn-dxf').on('click', () => this.descargar_dxf());
		$('#pd-btn-guardar').on('click', () => this.guardar_presupuesto());
		$('#pd-descuento').on('input', () => this.refresh_costos());
	}

	set_dist_mode(mode) {
		this.dist_mode = mode;
		$('#pd-dist-centradas').toggleClass('selected', mode === 'centradas');
		$('#pd-dist-cortar').toggleClass('selected', mode === 'cortar');
	}

	// Label de espesor: calibre para hierro (doble decapada) y galvanizada,
	// mm para el resto — misma convención que _abbreviated_label() del compiler.
	espesor_label(m) {
		const con_calibre =
			(m.familia === 'hierro' || m.familia === 'galvanizada') &&
			m.calibre && m.calibre !== '-';
		return con_calibre
			? 'N°' + m.calibre + ' (' + m.espesor_mm + 'mm)'
			: m.espesor_mm + ' mm';
	}

	on_material_change() {
		const mat = $('#pd-material').val();
		const sel = $('#pd-espesor');
		sel.empty().append('<option value="">—</option>').prop('disabled', true);
		if (!mat || !this.matIndex[mat]) return;
		this.matIndex[mat].forEach((m) =>
			sel.append($('<option>').val(m.espesor_mm).text(this.espesor_label(m)))
		);
		sel.prop('disabled', false);
		if (this.matIndex[mat].length === 1) sel.val(this.matIndex[mat][0].espesor_mm);
	}

	// ------------------------------------------------------------------
	// Lotes
	// ------------------------------------------------------------------

	add_batch() {
		const err = $('#pd-batch-error');
		err.addClass('hidden');
		try {
			const patron = this.selected_patron;
			const mat = $('#pd-material').val();
			const esp = parseFloat($('#pd-espesor').val());
			const cant = parseInt($('#pd-cantidad').val());
			const ancho = parseFloat($('#pd-ancho').val());
			const alto = parseFloat($('#pd-alto').val());
			const margen = parseFloat($('#pd-margen').val());

			if (!mat) throw new Error(__('Seleccioná un material.'));
			if (isNaN(esp) || esp <= 0) throw new Error(__('Seleccioná un espesor.'));
			if (isNaN(cant) || cant <= 0) throw new Error(__('Cantidad inválida.'));
			if (isNaN(ancho) || ancho <= 0) throw new Error(__('Ancho inválido.'));
			if (isNaN(alto) || alto <= 0) throw new Error(__('Alto inválido.'));
			if (isNaN(margen) || margen < 0) throw new Error(__('Margen inválido.'));

			const is_dxf = patron.startsWith('dxf:');
			const dxf_row = is_dxf ? this.patterns[parseInt(patron.slice(4))] : null;
			if (is_dxf && !dxf_row) throw new Error(__('Patrón DXF inválido — recargá la página.'));
			if (is_dxf && !dxf_row.file_available)
				throw new Error(__('El patrón no está disponible en el servidor todavía.'));

			const native_def = PanelDecorativo.NATIVE_PATTERNS.find((p) => p.val === patron);
			const batch = {
				panel_mode: is_dxf
					? 'dxf_pattern_grid'
					: patron.startsWith('cuadriculado')
					? 'cuadriculado'
					: patron,
				preset_name: is_dxf ? dxf_row.name : (native_def ? native_def.label : patron),
				pattern_type: 'nativo',
				cut_partial_figures: this.dist_mode === 'cortar',
				margin_mm: margen,
				material: mat,
				thickness_mm: esp,
				sheet_sizes: [[ancho, alto, cant]],
				hole_diameter_mm: 0,
				hole_distance_mm: 0,
				pattern_dxf_path: null,
				step_x_mm: null,
				step_y_mm: null,
			};

			if (is_dxf) {
				if (!dxf_row.file_path)
					throw new Error(__('El patrón DXF no tiene ruta de archivo.'));
				batch.pattern_dxf_path = dxf_row.file_path;
				// Paso X/Y heredado del patrón (fijado al cargarlo/calibrarlo) — no es un
				// input del panel.
				batch.step_x_mm = parseFloat(dxf_row.step_x);
				batch.step_y_mm = parseFloat(dxf_row.step_y);
				if (!(batch.step_x_mm > 0) || !(batch.step_y_mm > 0))
					throw new Error(__('El patrón "{0}" no tiene un paso X/Y válido cargado.', [dxf_row.name]));
			} else if (patron === 'tresbolillo') {
				batch.hole_diameter_mm = parseFloat($('#pd-diam').val());
				batch.hole_distance_mm = parseFloat($('#pd-dist').val());
				if (!(batch.hole_diameter_mm > 0)) throw new Error(__('Diámetro inválido.'));
				if (!(batch.hole_distance_mm > 0)) throw new Error(__('Separación inválida.'));
			} else if (patron.startsWith('cuadriculado')) {
				batch.hole_shape = patron === 'cuadriculado_square' ? 'square' : 'circle';
				batch.hole_size_mm = parseFloat($('#pd-hole-size').val());
				batch.offset_x_mm = parseFloat($('#pd-offset-x').val());
				batch.offset_y_mm = parseFloat($('#pd-offset-y').val());
				if (!(batch.hole_size_mm > 0)) throw new Error(__('Tamaño de agujero inválido.'));
				if (!(batch.offset_x_mm > 0) || !(batch.offset_y_mm > 0))
					throw new Error(__('Paso X/Y inválido.'));
			}

			this.batches.push(batch);
			this.render_batch_table();
		} catch (e) {
			err.text(e.message || String(e)).removeClass('hidden');
		}
	}

	remove_batch(idx) {
		this.batches.splice(idx, 1);
		this.render_batch_table();
	}

	render_batch_table() {
		const tbody = $('#pd-batch-tbody').empty();
		$('#pd-section-batches').toggleClass('hidden', !this.batches.length);
		this.batches.forEach((b, i) => {
			const sz = b.sheet_sizes[0];
			const tr = $('<tr>');
			tr.append($('<td>').text(b.preset_name));
			tr.append($('<td>').text(b.material + ' ' + b.thickness_mm + 'mm'));
			tr.append($('<td>').text(sz[0] + ' × ' + sz[1] + ' mm'));
			tr.append($('<td style="text-align:center">').text(sz[2]));
			tr.append(
				$('<td style="text-align:center">').append(
					$('<button class="btn btn-xs btn-default">✕</button>').on('click', () =>
						this.remove_batch(i)
					)
				)
			);
			tbody.append(tr);
		});
	}

	// ------------------------------------------------------------------
	// Calcular
	// ------------------------------------------------------------------

	calcular() {
		const err = $('#pd-calc-error').addClass('hidden');
		if (!this.batches.length) return;
		const btn = $('#pd-btn-calcular').prop('disabled', true).text(__('Calculando…'));
		frappe.call({
			method: 'sistema_industrial.api.paneles.calcular',
			args: {
				batches_json: JSON.stringify(this.batches),
				customer: this.get_customer(),
				job_name: $('#pd-job').val() || '',
				observations: '',
			},
			callback: (r) => {
				const msg = r.message || {};
				// Cada línea arranca con los 4 factores en 1 (MODELO_PRECIOS §2)
				this.lineas = (msg.lineas || []).map((ln) =>
					Object.assign({}, ln, {
						factor_kg: 1,
						factor_laser: 1,
						factor_plegar_kg: 1,
						factor_pliegue: 1,
					})
				);
				this.render_presupuesto(msg.warnings || []);
			},
			error: (e) => {
				err
					.text(__('Error al calcular: ') + ((e && e.message) || ''))
					.removeClass('hidden');
			},
			always: () => {
				btn.prop('disabled', false).text(__('Calcular presupuesto'));
			},
		});
	}

	// ------------------------------------------------------------------
	// Presupuesto — fórmula §3 de MODELO_PRECIOS.md
	// ------------------------------------------------------------------

	costo_linea(ln) {
		const mrow = this.material_row(ln.material, ln.espesor_mm) || {};
		const pKg = mrow.precio_por_kg || 0;
		const pPlegKg = mrow.precio_plegar_por_kg || 0;
		const pSeg = this.precios.precio_segundo_laser || 0;
		const pPliegue = this.precios.precio_por_plegado || 0;
		return (
			ln.peso_kg * pKg * ln.factor_kg +
			ln.tiempo_laser_s * pSeg * ln.factor_laser +
			ln.peso_kg * pPlegKg * ln.factor_plegar_kg +
			ln.cantidad_plegados * pPliegue * ln.factor_pliegue
		);
	}

	render_presupuesto(warnings) {
		$('#pd-section-presupuesto').removeClass('hidden');

		const wdiv = $('#pd-presu-warnings').empty();
		warnings.forEach((w) =>
			wdiv.append($('<div class="error-box" style="margin-bottom:8px">').text(w))
		);

		const tbody = $('#pd-presu-tbody').empty();
		this.lineas.forEach((ln, i) => {
			const tr = $('<tr>');
			tr.append($('<td>').text(ln.patron));
			tr.append($('<td>').text(ln.material + ' ' + ln.espesor_mm + 'mm × ' + ln.quantity));
			tr.append($('<td style="text-align:right">').text(ln.peso_kg.toFixed(2)));
			tr.append($('<td style="text-align:right">').text(ln.tiempo_laser_s.toFixed(0)));
			tr.append($('<td style="text-align:right">').text(ln.cantidad_plegados));
			['factor_kg', 'factor_laser', 'factor_plegar_kg', 'factor_pliegue'].forEach((f) => {
				const inp = $(
					'<input type="number" min="0" step="0.05" style="width:64px;text-align:center">'
				).val(ln[f]);
				inp.on('input', () => {
					const v = parseFloat(inp.val());
					ln[f] = isNaN(v) || v < 0 ? 0 : v;
					this.refresh_costos();
				});
				tr.append($('<td style="text-align:center">').append(inp));
			});
			tr.append(
				$('<td style="text-align:right;font-weight:600" class="pd-costo" data-i="' + i + '">')
			);
			tbody.append(tr);
		});
		this.refresh_costos();
	}

	refresh_costos() {
		let subtotal = 0;
		this.lineas.forEach((ln, i) => {
			const c = this.costo_linea(ln);
			subtotal += c;
			$('.pd-costo[data-i=' + i + ']').text(format_currency(c, 'ARS'));
		});
		const descuentoPct = parseFloat($('#pd-descuento').val()) || 0;
		const descuentoMonto = subtotal * (descuentoPct / 100);
		this.total_con_descuento = subtotal - descuentoMonto;
		this.descuento_pct = descuentoPct;
		$('#pd-presu-subtotal').text(format_currency(subtotal, 'ARS'));
		$('#pd-presu-descuento').text(
			descuentoPct > 0
				? '- ' + format_currency(descuentoMonto, 'ARS') + ' (' + descuentoPct + '%)'
				: '—'
		);
		$('#pd-presu-total').text(format_currency(this.total_con_descuento, 'ARS'));
	}

	// ------------------------------------------------------------------
	// DXF — POST con todos los lotes en el body, descarga automática del blob
	// ------------------------------------------------------------------

	// Secuencia de descarga (definida por Constantino):
	//   1. el usuario aprieta el botón
	//   2. se borra el DXF anterior (cliente y servidor)
	//   3. se genera el DXF nuevo
	//   4. mientras se genera, aparece "Generando DXF…"
	//   5. al terminar, recién ahí arranca la descarga automática
	async descargar_dxf() {
		if (!this.batches.length) return;
		const btn = $('#pd-btn-dxf');
		if (btn.prop('disabled')) return;   // paso 1: un solo disparo a la vez

		// Paso 2: borrar el DXF anterior (el de la descarga previa) ANTES de generar.
		if (this._lastObjUrl) {
			URL.revokeObjectURL(this._lastObjUrl);
			this._lastObjUrl = null;
		}

		const job = $('#pd-job').val() || 'panel';
		const filename = job.replace(/\s+/g, '_') + '.dxf';
		// El estado COMPLETO actual de los lotes viaja en el body del POST.
		const body = new FormData();
		body.append('batches_json', JSON.stringify(this.batches));
		body.append('customer', this.get_customer());
		body.append('job_name', job);

		// Paso 4: mensaje "Generando DXF…" mientras se genera (botón bloqueado).
		const orig = btn.text();
		btn.prop('disabled', true).text(__('Generando DXF…'));
		try {
			// Paso 3: generar el DXF nuevo. El backend borra el anterior y genera de cero.
			const resp = await fetch('/api/method/sistema_industrial.api.paneles.descargar_dxf', {
				method: 'POST',
				cache: 'no-store',
				headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
				body: body,
			});
			if (!resp.ok) throw new Error('HTTP ' + resp.status);
			const blob = await resp.blob();   // esperar a que TERMINE de generarse
			// Paso 5: recién ahí, descarga automática.
			this.auto_download(blob, filename);
			frappe.show_alert({ message: __('DXF descargado'), indicator: 'green' });
		} catch (e) {
			frappe.show_alert({ message: __('Error al descargar el DXF. Reintentá.'), indicator: 'red' });
		} finally {
			btn.prop('disabled', false).text(orig);
		}
	}

	// Descarga automática del blob recién generado (sin diálogo "dónde guardar").
	auto_download(blob, filename) {
		this._lastObjUrl = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = this._lastObjUrl;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		a.remove();
	}

	// ------------------------------------------------------------------
	// Guardar — SI Presupuesto Panel via frappe.client.insert
	// ------------------------------------------------------------------

	guardar_presupuesto() {
		const status = $('#pd-save-status').css('color', '').text('');
		if (!this.lineas.length) return;
		const customer = this.get_customer();
		if (!customer) {
			status.css('color', 'var(--si-red)').text(__('Falta el cliente.'));
			return;
		}
		const doc = {
			doctype: 'SI Presupuesto Panel',
			customer: customer,
			job_name: $('#pd-job').val() || '',
			descuento_pct: parseFloat($('#pd-descuento').val()) || 0,
			lineas: this.lineas.map((ln) => {
				const mrow = this.material_row(ln.material, ln.espesor_mm);
				return {
					patron: ln.patron,
					material_corte: mrow ? mrow.name : null,
					cantidad: ln.quantity,
					ancho_mm: ln.ancho_mm,
					alto_mm: ln.alto_mm,
					peso_kg: ln.peso_kg,
					tiempo_laser_s: ln.tiempo_laser_s,
					cantidad_plegados: ln.cantidad_plegados,
					factor_kg: ln.factor_kg,
					factor_laser: ln.factor_laser,
					factor_plegar_kg: ln.factor_plegar_kg,
					factor_pliegue: ln.factor_pliegue,
				};
			}),
		};
		status.text(__('Guardando…'));
		frappe.call({
			method: 'frappe.client.insert',
			args: { doc: doc },
			callback: (r) => {
				// El controller before_save recalcula costo_total/total_ars server-side
				status
					.css('color', 'var(--si-green)')
					.text(__('✓ Guardado: ') + r.message.name);
			},
			error: () => {
				status.css('color', 'var(--si-red)').text(__('Error al guardar.'));
			},
		});
	}
}
