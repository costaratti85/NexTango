frappe.pages['ocr-proveedores'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'OCR Proveedores',
		single_column: true,
	});
	$(frappe.render_template('ocr_proveedores', {})).appendTo(page.body);
	new OcrProveedores(page);
};

// Namespace REAL de los endpoints de Atlas (PR#12) — verificado en
// apps/.../api/ocr_proveedores.py. Métodos: subir_factura / estado / resultado /
// confirmar_recepcion_borrador. AISLADO acá + en el adaptador de payload de abajo:
// si el contrato final cambia nombres, se ajusta en un solo lugar.
const OCR_API = 'sistema_industrial.api.ocr_proveedores';
const OCR_POLL_MS = 2000;
// Bandas de color canónicas (Nova MSG_048): verde ≥85 · amarillo 50–84 · rojo <50.
const OCR_UMBRAL_VERDE = 85;
const OCR_UMBRAL_AMARILLO = 50;

// -------------------------------------------------------------------------
// Adaptador de payload: normaliza lo que devuelve resultado() de Atlas a la
// forma que consume la grilla. Es TOLERANTE — acepta los nombres reales de
// Atlas (idx, precio_unitario, match.score, match.reason, confianza a nivel de
// línea, proveedor.encontrado) Y los canónicos (id, precio, confianza, criterio,
// estado, layout_aprendido). Así anda contra el backend real y sigue andando si
// Atlas converge al canónico. El estado de color se deriva si el backend no lo manda.
// -------------------------------------------------------------------------
function ocrNormMatch(m, linea) {
	m = m || {};
	let conf = m.confianza != null ? m.confianza : (m.score != null ? m.score : (linea && linea.confianza != null ? linea.confianza : null));
	return {
		item_code: m.item_code != null ? m.item_code : null,
		item_name: m.item_name || '',
		confianza: conf != null ? Math.round(Number(conf)) : null,
		estado: m.estado || null,                       // Atlas no lo manda → se deriva
		criterio: m.criterio || m.reason || '',
	};
}
function ocrNormLinea(L, i) {
	L = L || {};
	const precio = L.precio != null ? L.precio : (L.precio_unitario != null ? L.precio_unitario : null);
	const cant = L.cantidad != null ? L.cantidad : null;
	const importe = L.importe != null ? L.importe : (cant != null && precio != null ? cant * precio : null);
	return {
		id: String(L.id != null ? L.id : (L.idx != null ? L.idx : i)),
		descripcion: L.descripcion || '',
		codigo_proveedor: L.codigo_proveedor || L.codigo_barras || '',
		cantidad: cant,
		precio: precio,
		importe: importe,
		iva: L.iva != null ? L.iva : null,
		match: L.match ? ocrNormMatch(L.match, L) : null,
		candidatos: (L.candidatos || []).map((c) => ocrNormMatch(c, L)),
	};
}
function ocrNormalize(raw) {
	raw = raw || {};
	const prov = raw.proveedor || {};
	const meta = raw.meta || {};
	const fact = raw.factura || meta.factura || {
		tipo: meta.tipo, numero: meta.numero, fecha: meta.fecha, total: meta.total, moneda: meta.moneda,
	};
	return {
		status: raw.status,
		umbral: raw.umbral != null ? raw.umbral : (meta.umbral != null ? meta.umbral : null),
		proveedor: {
			nombre: prov.nombre || '',
			cuit: prov.cuit || '',
			supplier: prov.supplier || null,
			layout_aprendido: prov.layout_aprendido != null ? prov.layout_aprendido : !!prov.encontrado,
		},
		factura: {
			tipo: fact.tipo || '', numero: fact.numero || '', fecha: fact.fecha || '',
			total: fact.total != null ? fact.total : null, moneda: fact.moneda || 'ARS',
		},
		warnings: raw.warnings || (raw.error ? [raw.error] : []),
		lineas: (raw.lineas || []).map(ocrNormLinea),
	};
}

class OcrProveedores {
	constructor(page) {
		this.page = page;
		this.file_url = null;
		this.file_label = null;
		this.job_id = null;
		this.data = null;          // payload YA normalizado
		this.decisiones = {};      // { line_id: { item_code, item_name, accion } }
		this._pollToken = 0;
		this.bind_events();
	}

	call_ocr(method, args) {
		return new Promise((resolve, reject) => {
			frappe.call({ method: OCR_API + '.' + method, args: args || {}, callback: (r) => resolve(r.message), error: reject });
		});
	}

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
	// 1) Subir factura → subir_factura (encola)
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
				this.job_id = m.job_id || m.invoice_id || null;
				if (!this.job_id) throw new Error('sin job_id');
				this.status(__('Procesando (OCR en cola)…'), '');
				this.poll();
			})
			.catch((e) => {
				if (this.is_not_published(e))
					this.status(__('El backend de OCR todavía no está publicado. Podés ver la grilla con "Ver ejemplo".'), 'var(--si-accent2)');
				else
					this.status(__('Error al enviar la factura. Revisá la consola.'), 'var(--si-red)');
			})
			.then(() => btn.prop('disabled', false));
	}

	// Poll liviano de estado(job_id); al terminar (done) trae resultado(job_id).
	// status de Atlas: queued | processing | done | error | ocr_pendiente | unknown.
	poll() {
		const token = ++this._pollToken;
		const tick = () => {
			if (token !== this._pollToken) return;
			this.call_ocr('estado', { job_id: this.job_id })
				.then((m) => {
					if (token !== this._pollToken) return;
					m = m || {};
					const st = m.status;
					if (st === 'done') {
						this.fetch_resultado();
					} else if (st === 'error') {
						this.status(__('El OCR falló: ') + (m.error || __('desconocido')), 'var(--si-red)');
					} else if (st === 'ocr_pendiente') {
						this.status(__('El motor OCR todavía no está publicado (el envío funciona). Probá "Ver ejemplo" mientras tanto.'), 'var(--si-accent2)');
					} else if (st === 'unknown') {
						this.status(__('El trabajo expiró o no existe. Reenviá la factura.'), 'var(--si-red)');
					} else {
						this.status((st === 'processing' ? __('Procesando OCR…') : __('En cola…')) + ' ⏳', '');
						setTimeout(tick, OCR_POLL_MS);
					}
				})
				.catch((e) => {
					if (token !== this._pollToken) return;
					if (this.is_not_published(e))
						this.status(__('El backend de OCR todavía no está publicado. Probá "Ver ejemplo".'), 'var(--si-accent2)');
					else
						this.status(__('Error consultando el estado. Revisá la consola.'), 'var(--si-red)');
				});
		};
		tick();
	}

	fetch_resultado() {
		this.call_ocr('resultado', { job_id: this.job_id })
			.then((raw) => {
				this.render(ocrNormalize(raw));
				this.status('✓ ' + __('Factura leída'), 'var(--si-green)');
			})
			.catch(() => this.status(__('Error al leer el resultado. Revisá la consola.'), 'var(--si-red)'));
	}

	cargar_demo() {
		this._pollToken++;   // corta cualquier poll en curso
		this.job_id = 'DEMO';
		this.status(__('Ejemplo cargado (no es una factura real)'), 'var(--si-muted)');
		this.render(ocrNormalize(OCR_DEMO_PAYLOAD));
	}

	// ------------------------------------------------------------------
	// 2) Grilla de revisión
	// ------------------------------------------------------------------

	// Estado por color. Lo decide el backend (match.estado) si viene; si no, se
	// deriva con las bandas canónicas: verde ≥85 · amarillo 50–84 · rojo <50.
	estado_de(match) {
		if (match && match.estado) return match.estado;
		if (!match || match.item_code == null || match.confianza == null) return 'rojo';
		const c = Number(match.confianza);
		if (c >= OCR_UMBRAL_VERDE) return 'verde';
		if (c >= OCR_UMBRAL_AMARILLO) return 'amarillo';
		return 'rojo';
	}

	render(payload) {
		this.data = payload || {};

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
		const u = this.data.umbral;
		$('#ocr-umbral').text(u != null ? __('Umbral: {0}', [u]) : __('verde ≥85 · amarillo 50–84 · rojo <50'));
		this.render_header();
		this.render_warnings();
		this.render_grid();
		this.render_summary();
	}

	render_header() {
		const p = this.data.proveedor || {};
		const f = this.data.factura || {};
		const $h = $('#ocr-header').empty();
		const cell = (k, v) => $h.append($('<div>').html('<b>' + frappe.utils.escape_html(k) + ':</b> ' + frappe.utils.escape_html(v == null || v === '' ? '—' : String(v))));
		cell(__('Proveedor'), p.nombre);
		cell(__('CUIT'), p.cuit);
		if (!p.supplier)
			$h.append($('<div class="ocr-h-warn">').text(__('⚠ sin Supplier en ERPNext')));
		else if (p.layout_aprendido)
			$h.append($('<div>').css('color', 'var(--si-green)').text(__('✓ layout aprendido')));
		cell(__('Comprobante'), ((f.tipo ? f.tipo + ' ' : '') + (f.numero || '')).trim());
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
		const moneda = (this.data.factura || {}).moneda || 'ARS';
		const tbody = $('#ocr-grid-tbody').empty();

		(this.data.lineas || []).forEach((ln) => {
			const dec = this.decisiones[ln.id];
			const match = ln.match || null;
			const estado = this.estado_de(match);
			const conf = match && match.confianza != null ? match.confianza : null;

			const tr = $('<tr>').attr('data-line', ln.id).addClass('ocr-' + estado);
			if (dec.accion === 'omitir') tr.addClass('ocr-omitida');

			tr.append($('<td>'));   // semáforo (borde de color por CSS)

			const $desc = $('<td>');
			$desc.append($('<div class="ocr-desc">').text(ln.descripcion || '—'));
			if (ln.codigo_proveedor)
				$desc.append($('<div class="ocr-codigo">').text(__('cód. prov.: ') + ln.codigo_proveedor));
			tr.append($desc);

			tr.append($('<td style="text-align:right">').text(ln.cantidad != null ? ln.cantidad : '—'));
			tr.append($('<td style="text-align:right">').text(ln.precio != null ? format_currency(ln.precio, moneda) : '—'));
			tr.append($('<td style="text-align:right">').text(ln.importe != null ? format_currency(ln.importe, moneda) : '—'));

			tr.append(this.render_item_cell(ln));

			const $conf = $('<td style="text-align:center">');
			$conf.append($('<span class="ocr-conf">').addClass('ocr-conf-' + estado).text(conf != null ? conf + '%' : '—'));
			tr.append($conf);

			const $act = $('<td style="text-align:center;white-space:nowrap">');
			$act.append($('<button class="btn btn-xs btn-default">').text(__('Ver candidatos')).on('click', () => this.ver_candidatos(ln)));
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
		dec.accion = dec.accion === 'omitir' ? 'confirmar' : 'omitir';
		this.refresh_row(ln);
	}

	// ------------------------------------------------------------------
	// Ver candidatos — candidatos vienen inline; fallback a buscar cualquier Item
	// ------------------------------------------------------------------

	ver_candidatos(ln) {
		this.dialogo_candidatos(ln, ln.candidatos || []);
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
		if (!candidatos.length)
			$l.append($('<div class="dimmed" style="margin-bottom:6px">').text(__('Sin candidatos automáticos. Buscá el Item abajo.')));
		candidatos.forEach((c) => {
			const row = $('<div class="ocr-cand-row">')
				.toggleClass('selected', c.item_code === dec.item_code)
				.on('click', () => { this.set_item(ln, c.item_code, c.item_name); d.hide(); });
			row.append(
				$('<div>').append($('<div class="ocr-cand-name">').text(c.item_name || c.item_code))
					.append($('<div class="ocr-cand-meta">').text((c.item_code || '') + (c.criterio ? ' · ' + c.criterio : '')))
			);
			row.append($('<div class="ocr-conf ocr-conf-' + this.estado_de(c) + '">').text((c.confianza != null ? c.confianza : '?') + '%'));
			$l.append(row);
		});
		d.get_field('lista').$wrapper.append($l);
		d.show();
	}

	set_item(ln, item_code, item_name) {
		const dec = this.decisiones[ln.id];
		dec.item_code = item_code;
		dec.item_name = item_name;
		dec.accion = 'confirmar';
		this.refresh_row(ln);
	}

	// ------------------------------------------------------------------
	// 3) Confirmar — Regla 8: el humano decide. Crea Purchase Receipt en BORRADOR
	//    (confirmar_recepcion_borrador de Atlas — nunca submit).
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
		$('#ocr-btn-confirmar').prop('disabled', sin > 0 || conf === 0);
	}

	// Líneas confirmadas → [{item_code, qty, rate}] (contrato de confirmar_recepcion_borrador)
	lineas_confirmadas() {
		const byId = {};
		(this.data.lineas || []).forEach((ln) => (byId[ln.id] = ln));
		return Object.keys(this.decisiones)
			.map((id) => ({ id: id, dec: this.decisiones[id], ln: byId[id] }))
			.filter((x) => x.dec.accion !== 'omitir' && x.dec.item_code && x.ln)
			.map((x) => ({ item_code: x.dec.item_code, qty: Number(x.ln.cantidad || 0), rate: Number(x.ln.precio || 0) }));
	}

	confirmar() {
		if (!this.data) return;
		const st = '#ocr-confirm-status';
		const sin = Object.keys(this.decisiones).filter((k) => this.decisiones[k].accion !== 'omitir' && !this.decisiones[k].item_code);
		if (sin.length) return this.status(__('Hay líneas sin Item. Elegí uno o omitilas.'), 'var(--si-red)', st);

		const lineas = this.lineas_confirmadas();
		if (!lineas.length) return this.status(__('No hay líneas confirmadas.'), 'var(--si-red)', st);

		if (this.job_id === 'DEMO' || !this.job_id)
			return this.status(__('Ejemplo: en una factura real, acá se crea la recepción en borrador.'), 'var(--si-muted)', st);

		const supplier = (this.data.proveedor || {}).supplier;
		if (!supplier)
			return this.status(__('Este proveedor no tiene Supplier en ERPNext, así que no se puede crear la recepción. (El alta de proveedor es zona Tango.)'), 'var(--si-red)', st);

		const btn = $('#ocr-btn-confirmar').prop('disabled', true);
		this.status(__('Confirmando…'), '', st);
		this.call_ocr('confirmar_recepcion_borrador', { supplier: supplier, lineas_json: JSON.stringify(lineas) })
			.then((m) => {
				m = m || {};
				if (m.ok) {
					this.status('✓ ' + __('Recepción en borrador creada: {0}', [m.purchase_receipt || '']), 'var(--si-green)', st);
					frappe.show_alert({ message: __('Recepción en borrador creada'), indicator: 'green' });
				} else {
					this.status(__('No se pudo confirmar: ') + (m.error || __('desconocido')), 'var(--si-red)', st);
				}
			})
			.catch((e) => {
				if (this.is_not_published(e))
					this.status(__('El backend de confirmación todavía no está publicado.'), 'var(--si-accent2)', st);
				else
					this.status(__('Error al confirmar. Revisá la consola.'), 'var(--si-red)', st);
			})
			.then(() => btn.prop('disabled', false));
	}
}

// Payload de ejemplo (modo demo, fallback opcional) — factura ficticia estilo
// "Cómodo", en la forma CANÓNICA. Sirve para ver/clickear la grilla sin backend.
const OCR_DEMO_PAYLOAD = {
	status: 'done',
	umbral: 85,
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
			match: { item_code: '01-05-0210', item_name: 'Chapa galvanizada Cal.24 1000x2000', confianza: 72, estado: 'amarillo', criterio: 'descripcion' },
			candidatos: [
				{ item_code: '01-05-0210', item_name: 'Chapa galvanizada Cal.24 1000x2000', confianza: 72, criterio: 'descripcion' },
				{ item_code: '01-05-0211', item_name: 'Chapa galvanizada Cal.25 1000x2000', confianza: 64, criterio: 'descripcion' },
			],
		},
		{
			id: 'l3', descripcion: 'DISCO CORTE 4.5 INOX x50', codigo_proveedor: 'DC45I',
			cantidad: 2, precio: 41840.25, importe: 83680.5, iva: 21,
			match: null,
			candidatos: [
				{ item_code: '05-02-0012', item_name: 'Disco de corte 4.5" metal', confianza: 41, criterio: 'descripcion' },
			],
		},
	],
};
