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

		this.bind_events();
		this.load_initial_data();
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
		$('#pd-patron').on('change', () => this.on_patron_change());
		$('#pd-btn-add').on('click', () => this.add_batch());
		$('#pd-btn-calcular').on('click', () => this.calcular());
		$('#pd-btn-dxf').on('click', () => this.descargar_dxf());
		$('#pd-btn-guardar').on('click', () => this.guardar_presupuesto());
	}

	on_material_change() {
		const mat = $('#pd-material').val();
		const sel = $('#pd-espesor');
		sel.empty().append('<option value="">—</option>').prop('disabled', true);
		if (!mat || !this.matIndex[mat]) return;
		this.matIndex[mat].forEach((m) =>
			sel.append($('<option>').val(m.espesor_mm).text(m.espesor_mm + ' mm'))
		);
		sel.prop('disabled', false);
		if (this.matIndex[mat].length === 1) sel.val(this.matIndex[mat][0].espesor_mm);
	}

	on_patron_change() {
		const p = $('#pd-patron').val();
		$('#pd-params-tresbolillo').toggleClass('hidden', p !== 'tresbolillo');
		$('#pd-params-cuadriculado').toggleClass(
			'hidden',
			p !== 'cuadriculado_circle' && p !== 'cuadriculado_square'
		);
	}

	// ------------------------------------------------------------------
	// Lotes
	// ------------------------------------------------------------------

	add_batch() {
		const err = $('#pd-batch-error');
		err.addClass('hidden');
		try {
			const patron = $('#pd-patron').val();
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

			const batch = {
				panel_mode: patron.startsWith('cuadriculado') ? 'cuadriculado' : patron,
				preset_name: $('#pd-patron option:selected').text(),
				pattern_type: 'nativo',
				cut_partial_figures: $('#pd-dist-mode').val() === 'cortar',
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

			if (patron === 'tresbolillo') {
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
				customer: $('#pd-customer').val() || '',
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
		let total = 0;
		this.lineas.forEach((ln, i) => {
			const c = this.costo_linea(ln);
			total += c;
			$('.pd-costo[data-i=' + i + ']').text(format_currency(c, 'ARS'));
		});
		$('#pd-presu-total').text(format_currency(total, 'ARS'));
	}

	// ------------------------------------------------------------------
	// DXF — opción B: URL binaria directa + showSaveFilePicker
	// ------------------------------------------------------------------

	descargar_dxf() {
		if (!this.batches.length) return;
		const job = $('#pd-job').val() || 'panel';
		const url =
			'/api/method/sistema_industrial.api.paneles.descargar_dxf' +
			'?batches_json=' + encodeURIComponent(JSON.stringify(this.batches)) +
			'&customer=' + encodeURIComponent($('#pd-customer').val() || '') +
			'&job_name=' + encodeURIComponent(job);
		this.save_dxf_as(url, job.replace(/\s+/g, '_') + '.dxf');
	}

	async save_dxf_as(url, filename) {
		// showSaveFilePicker donde exista (Chrome/Edge); fallback <a download>
		if (window.showSaveFilePicker) {
			try {
				const handle = await window.showSaveFilePicker({
					suggestedName: filename,
					types: [{ description: 'DXF', accept: { 'application/dxf': ['.dxf'] } }],
				});
				const resp = await fetch(url, { headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token } });
				if (!resp.ok) throw new Error('HTTP ' + resp.status);
				const writable = await handle.createWritable();
				await writable.write(await resp.blob());
				await writable.close();
				frappe.show_alert({ message: __('DXF guardado'), indicator: 'green' });
				return;
			} catch (e) {
				if (e && e.name === 'AbortError') return; // usuario canceló
				// caer al fallback
			}
		}
		const a = document.createElement('a');
		a.href = url;
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
		const customer = $('#pd-customer').val();
		if (!customer) {
			status.css('color', 'var(--si-red)').text(__('Falta el cliente.'));
			return;
		}
		const doc = {
			doctype: 'SI Presupuesto Panel',
			customer: customer,
			job_name: $('#pd-job').val() || '',
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
