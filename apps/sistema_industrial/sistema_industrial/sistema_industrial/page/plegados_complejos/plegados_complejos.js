frappe.pages['plegados-complejos'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Plegados Complejos',
		single_column: true,
	});
	$(wrapper).find('.page-content').html(frappe.render_template('plegados_complejos'));
	new PlegadosComplejos(page);
};

class PlegadosComplejos {
	constructor(page) {
		this.page = page;
		this.matIndex = {};      // {material: [rows de SI Material Corte]}
		this.precios = { precio_segundo_laser: 0, precio_por_plegado: 0 };
		this.resultado = null;   // último r.message ok de calcular()

		this.make_customer_control();
		this.bind_events();
		this.load_initial_data();
	}

	// ------------------------------------------------------------------
	// Carga inicial (mismo patrón que panel_decorativo)
	// ------------------------------------------------------------------

	make_customer_control() {
		this.customer_control = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Link',
				options: 'Customer',
				fieldname: 'customer',
				placeholder: __('Nombre o código de cliente'),
			},
			parent: $('#pc-customer-field'),
			render_input: true,
		});
	}

	get_customer() {
		return (this.customer_control && this.customer_control.get_value()) || '';
	}

	load_initial_data() {
		frappe.call({
			method: 'sistema_industrial.api.materiales.get_all',
			callback: (r) => {
				const rows = ((r.message || {}).rows || []).filter((m) => m.activo);
				this.matIndex = {};
				rows.forEach((m) => {
					if (!this.matIndex[m.material]) this.matIndex[m.material] = [];
					this.matIndex[m.material].push(m);
				});
				Object.values(this.matIndex).forEach((list) =>
					list.sort((a, b) => a.espesor_mm - b.espesor_mm)
				);
				const sel = $('#pc-material');
				sel.empty().append('<option value="">— elegir —</option>');
				Object.keys(this.matIndex)
					.sort()
					.forEach((name) => sel.append($('<option>').val(name).text(name)));
			},
			error: () => {
				$('#pc-material').html('<option value="">Error al cargar materiales</option>');
			},
		});

		frappe.call({
			method: 'sistema_industrial.api.materiales.get_precios',
			callback: (r) => {
				if (r.message) this.precios = r.message;
			},
		});
	}

	// Row seleccionada de SI Material Corte (material + espesor elegidos)
	selected_material_row() {
		const mat = $('#pc-material').val();
		const esp = parseFloat($('#pc-espesor').val());
		if (!mat || isNaN(esp)) return null;
		return (
			(this.matIndex[mat] || []).find((m) => Math.abs(m.espesor_mm - esp) < 0.001) ||
			null
		);
	}

	// ------------------------------------------------------------------
	// Eventos
	// ------------------------------------------------------------------

	bind_events() {
		$('#pc-material').on('change', () => {
			const mat = $('#pc-material').val();
			const sel = $('#pc-espesor');
			sel.empty().append('<option value="">—</option>').prop('disabled', true);
			if (!mat || !this.matIndex[mat]) return;
			this.matIndex[mat].forEach((m) =>
				sel.append($('<option>').val(m.espesor_mm).text(m.espesor_mm + ' mm'))
			);
			sel.prop('disabled', false);
			if (this.matIndex[mat].length === 1) sel.val(this.matIndex[mat][0].espesor_mm);
		});

		$('#pc-btn-calcular').on('click', () => this.calcular());
		$('#pc-btn-guardar').on('click', () => this.guardar_pedido());
		$('#pc-btn-dxf').on('click', () => this.descargar_dxf());

		['#pc-f-kg', '#pc-f-laser', '#pc-f-plegar-kg', '#pc-f-pliegue', '#pc-cantidad'].forEach(
			(id) => $(id).on('input', () => this.refresh_costos())
		);
	}

	// ------------------------------------------------------------------
	// Inputs / validación
	// ------------------------------------------------------------------

	read_geometria() {
		const mrow = this.selected_material_row();
		if (!mrow) throw new Error(__('Seleccioná material y espesor.'));
		const ancho = parseFloat($('#pc-ancho').val());
		const largo = parseFloat($('#pc-largo').val());
		const alto = parseFloat($('#pc-alto').val());
		if (isNaN(ancho) || ancho <= 0) throw new Error(__('Ancho interno inválido.'));
		if (isNaN(largo) || largo <= 0) throw new Error(__('Largo interno inválido.'));
		if (isNaN(alto) || alto <= 0) throw new Error(__('Alto inválido.'));
		if (alto <= mrow.espesor_mm)
			throw new Error(__('El alto debe ser mayor al espesor.'));
		return {
			material_corte: mrow.name,
			mrow: mrow,
			ancho_int: ancho,
			largo_int: largo,
			alto: alto,
			espesor: mrow.espesor_mm,
		};
	}

	get_factores() {
		const f = (id) => {
			const v = parseFloat($(id).val());
			return isNaN(v) || v < 0 ? 0 : v;
		};
		return {
			factor_kg: f('#pc-f-kg'),
			factor_laser: f('#pc-f-laser'),
			factor_plegar_kg: f('#pc-f-plegar-kg'),
			factor_pliegue: f('#pc-f-pliegue'),
		};
	}

	get_cantidad() {
		const c = parseInt($('#pc-cantidad').val());
		return isNaN(c) || c < 1 ? 1 : c;
	}

	// ------------------------------------------------------------------
	// Calcular
	// ------------------------------------------------------------------

	calcular() {
		const err = $('#pc-error').addClass('hidden');
		let geo;
		try {
			geo = this.read_geometria();
		} catch (e) {
			err.text(e.message).removeClass('hidden');
			return;
		}
		const btn = $('#pc-btn-calcular').prop('disabled', true).text(__('Calculando…'));
		frappe.call({
			method: 'sistema_industrial.api.plegados.calcular',
			args: {
				material_corte: geo.material_corte,
				ancho_int: geo.ancho_int,
				largo_int: geo.largo_int,
				alto: geo.alto,
				espesor: geo.espesor,
			},
			callback: (r) => {
				const msg = r.message || {};
				if (!msg.ok) {
					err.text(msg.error || __('Error desconocido.')).removeClass('hidden');
					$('#pc-section-resultado').addClass('hidden');
					this.resultado = null;
					return;
				}
				this.resultado = Object.assign({}, msg, { geo: geo });
				this.render_resultado();
			},
			always: () => {
				btn.prop('disabled', false).text(__('Calcular'));
			},
		});
	}

	render_resultado() {
		const r = this.resultado;
		$('#pc-section-resultado').removeClass('hidden');
		$('#pc-r-blank').text(r.blank_ancho.toFixed(0) + ' × ' + r.blank_largo.toFixed(0) + ' mm');
		$('#pc-r-despunte').text(r.despunte.toFixed(1) + ' mm');
		$('#pc-r-peso').text(r.kg_chapa.toFixed(3) + ' kg');
		$('#pc-r-laser').text(r.tiempo_laser_s.toFixed(0) + ' s');
		$('#pc-r-pliegues').text(r.plegados);
		this.refresh_costos();
	}

	// ------------------------------------------------------------------
	// Costos — fórmula §3 MODELO_PRECIOS.md, en vivo
	// ------------------------------------------------------------------

	refresh_costos() {
		const r = this.resultado;
		if (!r) return;
		const f = this.get_factores();
		const mrow = r.geo.mrow;
		const cKg = r.kg_chapa * (mrow.precio_por_kg || 0) * f.factor_kg;
		const cLaser = r.tiempo_laser_s * (this.precios.precio_segundo_laser || 0) * f.factor_laser;
		const cPlegKg = r.kg_chapa * (mrow.precio_plegar_por_kg || 0) * f.factor_plegar_kg;
		const cPliegue = r.plegados * (this.precios.precio_por_plegado || 0) * f.factor_pliegue;
		const unit = cKg + cLaser + cPlegKg + cPliegue;
		const cant = this.get_cantidad();

		$('#pc-c-kg').text(format_currency(cKg, 'ARS'));
		$('#pc-c-laser').text(format_currency(cLaser, 'ARS'));
		$('#pc-c-plegar-kg').text(format_currency(cPlegKg, 'ARS'));
		$('#pc-c-pliegue').text(format_currency(cPliegue, 'ARS'));
		$('#pc-c-unit').text(format_currency(unit, 'ARS'));
		$('#pc-c-cant').text(cant);
		$('#pc-c-total').text(format_currency(unit * cant, 'ARS'));
	}

	// ------------------------------------------------------------------
	// Guardar pedido
	// ------------------------------------------------------------------

	guardar_pedido() {
		const status = $('#pc-save-status').css('color', '').text('');
		const r = this.resultado;
		if (!r) return;
		const customer = this.get_customer();
		if (!customer) {
			status.css('color', 'var(--si-red)').text(__('Falta el cliente.'));
			return;
		}
		const f = this.get_factores();

		const data = Object.assign(
			{
				customer: customer,
				job_name: $('#pc-job').val() || '',
				material_corte: r.geo.material_corte,
				ancho_int: r.geo.ancho_int,
				largo_int: r.geo.largo_int,
				alto: r.geo.alto,
				espesor: r.geo.espesor,
				cantidad: this.get_cantidad(),
			},
			f
		);

		status.text(__('Guardando…'));
		frappe.call({
			method: 'sistema_industrial.api.plegados.guardar_pedido',
			args: { data_json: JSON.stringify(data) },
			callback: (resp) => {
				const m = resp.message || {};
				if (m.ok) {
					status
						.css('color', 'var(--si-green)')
						.text(__('✓ Guardado: ') + m.name + ' — ' + format_currency(m.costo_total, 'ARS'));
				} else {
					status.css('color', 'var(--si-red)').text(__('Error: ') + (m.error || ''));
				}
			},
			error: () => {
				status.css('color', 'var(--si-red)').text(__('Error al guardar.'));
			},
		});
	}

	// ------------------------------------------------------------------
	// DXF — fetch del binario y descarga automática del blob
	// ------------------------------------------------------------------

	// Secuencia de descarga (definida por Constantino):
	//   1. el usuario aprieta el botón
	//   2. se borra el DXF anterior (cliente y servidor)
	//   3. se genera el DXF nuevo
	//   4. mientras se genera, aparece "Generando DXF…"
	//   5. al terminar, recién ahí arranca la descarga automática
	async descargar_dxf() {
		const err = $('#pc-error').addClass('hidden');
		let geo;
		try {
			geo = this.read_geometria();
		} catch (e) {
			err.text(e.message).removeClass('hidden');
			return;
		}
		const btn = $('#pc-btn-dxf');
		if (btn.prop('disabled')) return;   // paso 1: un solo disparo a la vez

		// Paso 2: borrar el DXF anterior (el de la descarga previa) ANTES de generar.
		if (this._lastObjUrl) {
			URL.revokeObjectURL(this._lastObjUrl);
			this._lastObjUrl = null;
		}

		const job = $('#pc-job').val() || 'bandeja';
		const url =
			'/api/method/sistema_industrial.api.plegados.descargar_dxf' +
			'?material_corte=' + encodeURIComponent(geo.material_corte) +
			'&ancho_int=' + geo.ancho_int +
			'&largo_int=' + geo.largo_int +
			'&alto=' + geo.alto +
			'&espesor=' + geo.espesor +
			'&job_name=' + encodeURIComponent(job);
		const filename = job.replace(/\s+/g, '_') + '.dxf';

		// Paso 4: mensaje "Generando DXF…" mientras se genera (botón bloqueado).
		const orig = btn.text();
		btn.prop('disabled', true).text(__('Generando DXF…'));
		try {
			// Paso 3: generar el DXF nuevo. El backend borra el anterior y genera de cero.
			const resp = await fetch(url, {
				cache: 'no-store',
				headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
			});
			if (!resp.ok) throw new Error('HTTP ' + resp.status);
			const blob = await resp.blob();   // esperar a que TERMINE de generarse
			// Paso 5: recién ahí, descarga automática.
			this.auto_download(blob, filename);
			frappe.show_alert({ message: __('DXF descargado'), indicator: 'green' });
		} catch (e) {
			err.text(__('Error al descargar el DXF. Reintentá.')).removeClass('hidden');
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
}
