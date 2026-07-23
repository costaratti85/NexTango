frappe.pages['ocr-proveedores'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'OCR Proveedores',
		single_column: true,
	});
	$(frappe.render_template('ocr_proveedores', {})).appendTo(page.body);
	new OcrProveedores(page);
};

// Namespace del backend de OCR (Atlas/OCR). AISLADO: si el contrato final cambia
// el nombre del módulo o de los métodos, se ajusta acá y en call_ocr().
const OCR_API = 'sistema_industrial.ocr_suppliers.api';
const OCR_POLL_MS = 2000;
const OCR_UMBRAL_DEFAULT = 82;

class OcrProveedores {
	constructor(page) {
		this.page = page;
		this.file_url = null;
		this.file_label = null;
		this.invoice_id = null;
		this.data = null;          // payload de get_resultado
		this.decisiones = {};      // { line_id: { item_code, item_name, accion } }
		this._pollToken = 0;       // invalida polls viejos
		this.bind_events();
	}

	// Llamada al backend, aislada. Devuelve Promise<message>. Rechaza en error.
	call_ocr(method, args) {
		return new Promise((resolve, reject) => {
			frappe.call({ method: OCR_API + '.' + method, args: args || {}, callback: (r) => resolve(r.message), error: reject });
		});
	}

	// ¿El error es "endpoint todavía no publicado"? (backend de Atlas/OCR en curso)
	is_not_published(e) {
		return /does not exist|not found|AttributeError|ModuleNotFound|404/i.test(JSON.stringify(e || {}));
	}

	bind_events() {
		$('#ocr-drop').on('click', () => this.pick_file());
		$('#ocr-btn-procesar').on('click', () => this.procesar());
		$('#ocr-btn-demo').on('click', () => this.cargar_demo());
		$('#ocr-btn-confirmar').on('click', () => this.confirmar());
	}

	status(msg, color, id) {
		$(id || '#ocr-status').css('color', color || '').text(msg || '');
	}

	// ------------------------------------------------------------------
	// 1) Subir factura
	// ------------------------------------------------------------------

	pick_file() {
		new frappe.ui.FileUploader({
			as_dataurl: false,
			allow_multiple: false,
			restrictions: { allowed_file_types: ['.pdf', '.jpg', '.jpeg', '.png'] },
			make_attachments_public: false,
			on_success: (file_doc) => {
				this.file_url = file_doc.file_url;
				this.file_label = file_doc.file_name || file_doc.file_url;
				$('#ocr-drop-prompt').addClass('hidden');
				$('#ocr-file-name').removeClass('hidden').text('✓ ' + this.file_label);
				$('#ocr-drop').addClass('has-file');
				$('#ocr-btn-procesar').prop('disabled', false);
			},
		});
	}

	procesar() {
		if (!this.file_url) return;
		const btn = $('#ocr-btn-procesar').prop('disabled', true);
		this.status(__('Enviando al servidor…'), '');
		this.call_ocr('subir_factura', { file_url: this.file_url })
			.then((m) => {
				m = m || {};
				this.invoice_id = m.invoice_id || null;
				if (!this.invoice_id) throw new Error('sin invoice_id');
				this.status(__('Procesando (OCR en cola)…'), '');
				this.poll();
			})
			.catch((e) => {
				if (this.is_not_published(e)) {
					this.status(
						__('El backend de OCR todavía no está publicado. Podés ver la grilla con "Ver ejemplo".'),
						'var(--si-accent2)'
					);
				} else {
					this.status(__('Error al enviar la factura. Revisá la consola.'), 'var(--si-red)');
				}
			})
			.then(() => btn.prop('disabled', false));
	}

	poll() {
		const token = ++this._pollToken;
		const tick = () => {
			if (token !== this._pollToken) return;   // cancelado por otra corrida
			this.call_ocr('get_resultado', { invoice_id: this.invoice_id })
				.then((m) => {
					if (token !== this._pollToken) return;
					m = m || {};
					if (m.status === 'listo') {
						this.render(m);
						this.status('✓ ' + __('Factura leída'), 'var(--si-green)');
					} else if (m.status === 'error') {
						this.status(__('El OCR falló: ') + (m.error || __('desconocido')), 'var(--si-red)');
					} else {
						this.status((m.progreso || __('Procesando…')) + ' ⏳', '');
						setTimeout(tick, OCR_POLL_MS);
					}
				})
				.catch(() => {
					if (token !== this._pollToken) return;
					this.status(__('Error consultando el resultado. Revisá la consola.'), 'var(--si-red)');
				});
		};
		tick();
	}

	cargar_demo() {
		this._pollToken++;   // corta cualquier poll en curso
		this.invoice_id = 'DEMO';
		this.status(__('Ejemplo cargado (no es una factura real)'), 'var(--si-muted)');
		this.render(OCR_DEMO_PAYLOAD);
	}

	// ------------------------------------------------------------------
	// 2) Grilla de revisión
	// ------------------------------------------------------------------

	// Estado por color: lo decide OCR/backend (match.estado). Fallback por confianza.
	estado_de(match, umbral) {
		if (match && match.estado) return match.estado;
		if (!match || match.item_code == null) return 'rojo';
		const c = Number(match.confianza || 0);
		if (c >= umbral) return 'verde';
		if (c >= umbral - 15) return 'amarillo';
		return 'rojo';
	}

	render(payload) {
		this.data = payload || {};
		const umbral = this.data.umbral || OCR_UMBRAL_DEFAULT;

		// decisiones default: item del match; omitir si no hay item
		this.decisiones = {};
		(this.data.lineas || []).forEach((ln) => {
			const has = ln.match && ln.match.item_code != null;
			this.decisiones[ln.id] = {
				item_code: has ? ln.match.item_code : null,
				item_name: has ? ln.match.item_name : null,
				accion: has ? 'confirmar' : 'omitir',
			};
		});

		$('#ocr-section-review').removeClass('hidden');
		$('#ocr-umbral').text(__('Umbral de confianza: {0}', [umbral]));
		this.render_header();
		this.render_warnings();
		this.render_grid();
		this.render_summary();
	}

	render_header() {
		const p = this.data.proveedor || {};
		const f = this.data.factura || {};
		const $h = $('#ocr-header').empty();
		const cell = (k, v) => $h.append($('<div>').html('<b>' + frappe.utils.escape_html(k) + ':</b> ' + frappe.utils.escape_html(v == null ? '—' : String(v))));
		cell(__('Proveedor'), p.nombre);
		cell(__('CUIT'), p.cuit);
		if (!p.supplier)
			$h.append($('<div class="ocr-h-warn">').text(__('⚠ sin Supplier en ERPNext')));
		else if (p.layout_aprendido)
			$h.append($('<div>').css('color', 'var(--si-green)').text(__('✓ layout aprendido')));
		cell(__('Comprobante'), (f.tipo ? f.tipo + ' ' : '') + (f.numero || ''));
		cell(__('Fecha'), f.fecha);
		cell(__('Total'), f.total != null ? format_currency(f.total, f.moneda || 'ARS') : '—');
	}

	render_warnings() {
		const $w = $('#ocr-warnings').empty();
		(this.data.warnings || []).forEach((t) =>
			$w.append($('<div class="error-box" style="margin-bottom:8px">').text(t))
		);
	}

	render_grid() {
		const umbral = this.data.umbral || OCR_UMBRAL_DEFAULT;
		const tbody = $('#ocr-grid-tbody').empty();

		(this.data.lineas || []).forEach((ln) => {
			const dec = this.decisiones[ln.id];
			const match = ln.match || null;
			const estado = this.estado_de(match, umbral);
			const conf = match ? Number(match.confianza || 0) : 0;

			const tr = $('<tr>').attr('data-line', ln.id).addClass('ocr-' + estado);
			if (dec.accion === 'omitir') tr.addClass('ocr-omitida');

			tr.append($('<td>'));   // celda del semáforo (borde de color por CSS)

			// Descripción + código proveedor
			const $desc = $('<td>');
			$desc.append($('<div class="ocr-desc">').text(ln.descripcion || '—'));
			if (ln.codigo_proveedor)
				$desc.append($('<div class="ocr-codigo">').text(__('cód. prov.: ') + ln.codigo_proveedor));
			tr.append($desc);

			tr.append($('<td style="text-align:right">').text(ln.cantidad != null ? ln.cantidad : '—'));
			tr.append($('<td style="text-align:right">').text(ln.precio != null ? format_currency(ln.precio, (this.data.factura || {}).moneda || 'ARS') : '—'));
			tr.append($('<td style="text-align:right">').text(ln.importe != null ? format_currency(ln.importe, (this.data.factura || {}).moneda || 'ARS') : '—'));

			// Item de ERPNext (elegido, editable)
			tr.append(this.render_item_cell(ln));

			// Confianza
			const $conf = $('<td style="text-align:center">');
			$conf.append(
				$('<span class="ocr-conf">').addClass('ocr-conf-' + estado).text(match ? conf + '%' : '—')
			);
			tr.append($conf);

			// Acción: ver candidatos + omitir/incluir
			const $act = $('<td style="text-align:center;white-space:nowrap">');
			$act.append(
				$('<button class="btn btn-xs btn-default">').text(__('Ver candidatos')).on('click', () => this.ver_candidatos(ln))
			);
			$act.append(
				$('<button class="btn btn-xs btn-default" style="margin-left:5px">')
					.text(dec.accion === 'omitir' ? __('Incluir') : __('Omitir'))
					.on('click', () => this.toggle_omitir(ln))
			);
			tr.append($act);

			tbody.append(tr);
		});
	}

	render_item_cell(ln) {
		const dec = this.decisiones[ln.id];
		const $td = $('<td class="ocr-item-cell">');
		if (dec.item_code) {
			$td.append($('<div class="ocr-item-name">').text(dec.item_name || dec.item_code));
			$td.append($('<div class="ocr-item-code">').text(dec.item_code));
			if (ln.match && ln.match.item_code === dec.item_code && ln.match.criterio)
				$td.append($('<div class="ocr-criterio">').text(__('match por ') + ln.match.criterio));
		} else {
			$td.append($('<span class="ocr-item-none">').text(__('sin Item — elegí uno')));
		}
		return $td;
	}

	// Reemplaza la celda de Item y el estado visual de una fila sin re-render total
	refresh_row(ln) {
		const $tr = $('#ocr-grid-tbody tr[data-line="' + ln.id + '"]');
		if (!$tr.length) return;
		const dec = this.decisiones[ln.id];
		$tr.find('.ocr-item-cell').replaceWith(this.render_item_cell(ln));
		$tr.toggleClass('ocr-omitida', dec.accion === 'omitir');
		$tr.find('td:last-child .btn:last-child').text(dec.accion === 'omitir' ? __('Incluir') : __('Omitir'));
		this.render_summary();
	}

	toggle_omitir(ln) {
		const dec = this.decisiones[ln.id];
		if (dec.accion === 'omitir') {
			// volver a incluir: si no hay item elegido, no se puede confirmar todavía
			dec.accion = 'confirmar';
		} else {
			dec.accion = 'omitir';
		}
		this.refresh_row(ln);
	}

	// ------------------------------------------------------------------
	// Ver candidatos — elegir alternativa (o buscar cualquier Item)
	// ------------------------------------------------------------------

	ver_candidatos(ln) {
		const armar = (candidatos) => this.dialogo_candidatos(ln, candidatos || []);
		if (ln.candidatos && ln.candidatos.length) return armar(ln.candidatos);
		if (this.invoice_id === 'DEMO' || !this.invoice_id) return armar([]);
		// lazy: pedirlos al backend
		this.call_ocr('get_candidatos', { invoice_id: this.invoice_id, line_id: ln.id })
			.then((m) => armar((m || {}).candidatos || []))
			.catch(() => armar([]));   // si no existe el endpoint, igual dejamos buscar Item
	}

	dialogo_candidatos(ln, candidatos) {
		const dec = this.decisiones[ln.id];
		const d = new frappe.ui.Dialog({
			title: __('Elegir Item para: {0}', [ln.descripcion || '—']),
			fields: [
				{ fieldtype: 'HTML', fieldname: 'lista' },
				{ fieldtype: 'Section Break', label: __('O buscar cualquier Item') },
				{ fieldtype: 'Link', fieldname: 'item', label: __('Item'), options: 'Item' },
			],
			primary_action_label: __('Usar este Item'),
			primary_action: (v) => {
				if (!v.item) return frappe.msgprint(__('Elegí un Item de la lista o del buscador.'));
				frappe.db.get_value('Item', v.item, 'item_name').then((r) => {
					this.set_item(ln, v.item, (r.message && r.message.item_name) || v.item);
					d.hide();
				});
			},
		});

		const $l = $('<div>');
		if (!candidatos.length) {
			$l.append($('<div class="dimmed" style="margin-bottom:6px">').text(__('Sin candidatos automáticos. Buscá el Item abajo.')));
		}
		candidatos.forEach((c) => {
			const row = $('<div class="ocr-cand-row">')
				.toggleClass('selected', c.item_code === dec.item_code)
				.on('click', () => {
					this.set_item(ln, c.item_code, c.item_name);
					d.hide();
				});
			row.append(
				$('<div>').append($('<div class="ocr-cand-name">').text(c.item_name || c.item_code))
					.append($('<div class="ocr-cand-meta">').text((c.item_code || '') + (c.criterio ? ' · ' + c.criterio : '')))
			);
			row.append($('<div class="ocr-conf ocr-conf-' + this.estado_de(c, this.data.umbral || OCR_UMBRAL_DEFAULT) + '">').text((c.confianza != null ? c.confianza : '?') + '%'));
			$l.append(row);
		});
		d.get_field('lista').$wrapper.append($l);
		d.show();
	}

	set_item(ln, item_code, item_name) {
		const dec = this.decisiones[ln.id];
		dec.item_code = item_code;
		dec.item_name = item_name;
		dec.accion = 'confirmar';   // elegir un item = incluir la línea
		this.refresh_row(ln);
	}

	// ------------------------------------------------------------------
	// 3) Confirmar — Regla 8: el humano decide
	// ------------------------------------------------------------------

	render_summary() {
		let conf = 0, omit = 0, sin = 0;
		Object.keys(this.decisiones).forEach((k) => {
			const d = this.decisiones[k];
			if (d.accion === 'omitir') omit++;
			else if (d.item_code) conf++;
			else sin++;
		});
		let txt = __('{0} a confirmar · {1} omitidas', [conf, omit]);
		if (sin) txt += ' · ' + __('{0} sin Item (elegí o omití)', [sin]);
		$('#ocr-confirm-summary').text(txt);
		$('#ocr-btn-confirmar').prop('disabled', sin > 0);
	}

	confirmar() {
		if (!this.data) return;
		const sin = Object.keys(this.decisiones).filter((k) => this.decisiones[k].accion !== 'omitir' && !this.decisiones[k].item_code);
		if (sin.length) return this.status(__('Hay líneas sin Item. Elegí uno o omitilas.'), 'var(--si-red)', '#ocr-confirm-status');

		const decisiones = Object.keys(this.decisiones).map((line_id) => ({
			line_id: line_id,
			item_code: this.decisiones[line_id].item_code,
			accion: this.decisiones[line_id].accion,
		}));

		if (this.invoice_id === 'DEMO' || !this.invoice_id) {
			return this.status(__('Ejemplo: en una factura real, acá se confirma la revisión.'), 'var(--si-muted)', '#ocr-confirm-status');
		}

		const btn = $('#ocr-btn-confirmar').prop('disabled', true);
		this.status(__('Confirmando…'), '', '#ocr-confirm-status');
		this.call_ocr('confirmar', { invoice_id: this.invoice_id, decisiones_json: JSON.stringify(decisiones) })
			.then((m) => {
				m = m || {};
				if (m.ok) {
					this.status('✓ ' + (m.resumen || __('Revisión confirmada')), 'var(--si-green)', '#ocr-confirm-status');
					frappe.show_alert({ message: __('Revisión confirmada'), indicator: 'green' });
				} else {
					this.status(__('No se pudo confirmar: ') + (m.error || __('desconocido')), 'var(--si-red)', '#ocr-confirm-status');
				}
			})
			.catch((e) => {
				if (this.is_not_published(e))
					this.status(__('El backend de confirmación todavía no está publicado.'), 'var(--si-accent2)', '#ocr-confirm-status');
				else
					this.status(__('Error al confirmar. Revisá la consola.'), 'var(--si-red)', '#ocr-confirm-status');
			})
			.then(() => btn.prop('disabled', false));
	}
}

// Payload de ejemplo (modo demo) — factura ficticia estilo "Cómodo", para que
// Constantino vea/clickee la grilla sin depender del backend. NO es real.
const OCR_DEMO_PAYLOAD = {
	status: 'listo',
	umbral: 82,
	proveedor: { nombre: 'Cómodo S.A. (EJEMPLO)', cuit: '30-70000000-0', supplier: 'Cómodo S.A.', layout_aprendido: true },
	factura: { tipo: 'A', numero: '0001-00012345', fecha: '2026-07-20', total: 154230.5, moneda: 'ARS' },
	warnings: ['Ejemplo de demostración — los datos no provienen de una factura real.'],
	lineas: [
		{
			id: 'l1', descripcion: 'TORNILLO HEXAGONAL 1/4 x 2', codigo_proveedor: 'TH14X2',
			cantidad: 100, precio: 85.5, importe: 8550, iva: 21,
			match: { item_code: '02-01-0033', item_name: 'Tornillo hexagonal 1/4" x 2"', confianza: 96, estado: 'verde', criterio: 'codigo' },
			candidatos: [
				{ item_code: '02-01-0033', item_name: 'Tornillo hexagonal 1/4" x 2"', confianza: 96, criterio: 'codigo' },
				{ item_code: '02-01-0034', item_name: 'Tornillo hexagonal 1/4" x 2.5"', confianza: 71, criterio: 'descripcion' },
			],
		},
		{
			id: 'l2', descripcion: 'CHAPA GALV C24 1000x2000', codigo_proveedor: '',
			cantidad: 5, precio: 12400, importe: 62000, iva: 21,
			match: { item_code: '01-05-0210', item_name: 'Chapa galvanizada Cal.24 1000x2000', confianza: 84, estado: 'amarillo', criterio: 'descripcion' },
			candidatos: [
				{ item_code: '01-05-0210', item_name: 'Chapa galvanizada Cal.24 1000x2000', confianza: 84, criterio: 'descripcion' },
				{ item_code: '01-05-0211', item_name: 'Chapa galvanizada Cal.25 1000x2000', confianza: 79, criterio: 'descripcion' },
				{ item_code: '01-05-0208', item_name: 'Chapa galvanizada Cal.24 1220x2440', confianza: 68, criterio: 'descripcion' },
			],
		},
		{
			id: 'l3', descripcion: 'DISCO CORTE 4.5 INOX x50', codigo_proveedor: 'DC45I',
			cantidad: 2, precio: 41840.25, importe: 83680.5, iva: 21,
			match: null,
			candidatos: [
				{ item_code: '05-02-0012', item_name: 'Disco de corte 4.5" metal', confianza: 61, criterio: 'descripcion' },
			],
		},
	],
};
