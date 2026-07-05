frappe.pages['corte-barras'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Corte de Barras',
		single_column: true,
	});

	$(frappe.render_template('corte_barras', {})).appendTo(page.body);
	new CorteBarras(page);
};

class CorteBarras {
	constructor(page) {
		this.page = page;
		this.calculating = false;
		this._make_customer_control();
		this._make_item_control();
		this._bind_events();
	}

	// ── Frappe Link controls ──────────────────────────────────────────────────

	_make_customer_control() {
		this.customer_ctrl = frappe.ui.form.make_control({
			parent: $('#cb-customer-field'),
			df: {
				fieldtype: 'Link',
				fieldname: 'customer',
				options: 'Customer',
				placeholder: __('Buscar cliente...'),
			},
			render_input: true,
		});
		sistema_industrial.attach_customer_sync_button(this.customer_ctrl, '#cb-customer-field');
	}

	_make_item_control() {
		this.item_ctrl = frappe.ui.form.make_control({
			parent: $('#cb-item-field'),
			df: {
				fieldtype: 'Link',
				fieldname: 'item',
				options: 'Item',
				placeholder: __('Buscar perfil o caño (01-/02-)...'),
				// search_link no soporta or_filters (confirmado: TypeError) — filters
				// ANDados de "like 01-%" + "like 02-%" es una condición imposible,
				// siempre devolvía 0 resultados. Resuelto con query function propia.
				get_query: () => ({ query: 'sistema_industrial.api.corte_barras.item_query' }),
			},
			render_input: true,
		});
	}

	// ── Eventos ───────────────────────────────────────────────────────────────

	_bind_events() {
		$('#cb-btn-add').on('click', () => this._add_row());
		$('#cb-pieces-body').on('click', '.cb-del-row', (e) => {
			const rows = $('#cb-pieces-body tr');
			if (rows.length > 1) $(e.currentTarget).closest('tr').remove();
		});
		$('#cb-btn-calc').on('click', () => this._calcular());
	}

	// ── Tabla de piezas ───────────────────────────────────────────────────────

	_add_row() {
		const tr = $(`
			<tr>
				<td><input type="number" class="cb-qty" value="1" min="1" step="1"></td>
				<td><input type="number" class="cb-len" min="1" step="1" placeholder="mm"></td>
				<td><button class="cb-del-row cb-ghost-sm">✕</button></td>
			</tr>`);
		$('#cb-pieces-body').append(tr);
		tr.find('.cb-len').focus();
	}

	_get_cuts() {
		const cuts = [];
		$('#cb-pieces-body tr').each(function () {
			const qty = parseInt($(this).find('.cb-qty').val(), 10) || 0;
			const len = parseFloat($(this).find('.cb-len').val()) || 0;
			if (qty > 0 && len > 0) cuts.push([qty, len]);
		});
		return cuts;
	}

	// ── Cálculo ───────────────────────────────────────────────────────────────

	_calcular() {
		if (this.calculating) return;

		const cuts = this._get_cuts();
		if (!cuts.length) {
			this._show_error('Ingresá al menos una fila con cantidad y largo.');
			return;
		}

		const bar_len = parseFloat($('#cb-bar-len').val()) || 0;
		const kerf_mm = parseFloat($('#cb-kerf').val()) ?? 2;
		const price_per_bar = parseFloat($('#cb-price-bar').val()) || 0;
		const price_per_meter = parseFloat($('#cb-price-metro').val()) || 0;

		if (bar_len <= 0) {
			this._show_error('El largo de barra debe ser mayor a 0.');
			return;
		}

		this._hide_error();
		this._set_loading(true);

		frappe.call({
			method: 'sistema_industrial.api.corte_barras.calcular',
			args: {
				bar_len,
				cuts_json: JSON.stringify(cuts),
				price_per_bar,
				price_per_meter,
				kerf_mm,
			},
			callback: (r) => {
				this._set_loading(false);
				if (r.exc || !r.message) {
					this._show_error('Error al calcular. Revisá los datos.');
					return;
				}
				this._render_results(r.message);
			},
			error: () => {
				this._set_loading(false);
				this._show_error('Error de conexión con el servidor.');
			},
		});
	}

	// ── Renderizado de resultados ─────────────────────────────────────────────

	_render_results(data) {
		if (data.error) {
			this._show_error(data.error);
			$('#cb-results').hide();
			return;
		}

		// KPIs
		const kpis_html = `
			<div class="cb-kpi highlight">
				<div class="k">Barras enteras</div>
				<div class="v">${data.full_bars}</div>
				<div class="u">unidades</div>
			</div>
			<div class="cb-kpi">
				<div class="k">Tramo suelto</div>
				<div class="v">${data.tramo_total_meters.toFixed(2)}</div>
				<div class="u">metros</div>
			</div>
			<div class="cb-kpi highlight">
				<div class="k">Costo total</div>
				<div class="v">${this._fmt_pesos(data.total_cost)}</div>
				<div class="u">ARS</div>
			</div>
			${data.full_bars > 0 ? `<div class="cb-kpi">
				<div class="k">Eficiencia barras</div>
				<div class="v">${data.global_efficiency_pct.toFixed(1)}</div>
				<div class="u">%</div>
			</div>` : ''}
		`;
		$('#cb-kpis').html(kpis_html);

		// Desglose de costos
		const has_prices = data.full_bar_cost > 0 || data.tramo_cost > 0;
		if (has_prices) {
			$('#cb-cost-breakdown').html(`
				<div class="cb-breakdown">
					${data.full_bars > 0 ? `<div class="line">
						<span>${data.full_bars} barra${data.full_bars !== 1 ? 's' : ''}</span>
						<span>${this._fmt_pesos(data.full_bar_cost)}</span>
					</div>` : ''}
					${data.tramo_total_meters > 0 ? `<div class="line sub">
						<span>${data.tramo_total_meters.toFixed(3)} m tramo suelto</span>
						<span>${this._fmt_pesos(data.tramo_cost)}</span>
					</div>` : ''}
					<div class="line total">
						<span>Total</span>
						<span>${this._fmt_pesos(data.total_cost)}</span>
					</div>
				</div>`);
		} else {
			$('#cb-cost-breakdown').html('');
		}

		// Plan de corte
		if (data.bar_patterns && data.bar_patterns.length > 0) {
			let rows_html = '';
			data.bar_patterns.forEach((p, i) => {
				const chips = p.pieces.map(mm => `<span class="cb-chip">${mm}</span>`).join('');
				rows_html += `<tr>
					<td>${i + 1}</td>
					<td><div class="cb-pattern-chips">${chips}</div></td>
					<td><b>${p.count}</b></td>
					<td>${p.used_mm.toLocaleString()} mm</td>
					<td>${p.waste_mm.toLocaleString()} mm</td>
					<td>${p.efficiency_pct.toFixed(1)}%</td>
				</tr>`;
			});
			$('#cb-plan-body').html(rows_html);
			$('#cb-plan-card').show();
		} else {
			$('#cb-plan-card').hide();
		}

		// Tramos sueltos
		if (data.tramo_pieces && data.tramo_pieces.length > 0) {
			const chips = data.tramo_pieces.map(mm =>
				`<span class="cb-tramo-chip">${mm} mm</span>`
			).join('');
			$('#cb-tramos-list').html(`
				<div class="cb-tramos-grid">${chips}</div>
				<p style="margin-top:10px;color:#5b7390;font-size:14px;">
					Total: ${data.tramo_total_meters.toFixed(3)} m
					(${data.tramo_pieces.length} pieza${data.tramo_pieces.length !== 1 ? 's' : ''})
				</p>`);
			$('#cb-tramos-card').show();
		} else {
			$('#cb-tramos-card').hide();
		}

		$('#cb-results').show();
	}

	// ── UI helpers ────────────────────────────────────────────────────────────

	_fmt_pesos(n) {
		if (!n) return '$0';
		return '$' + n.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
	}

	_set_loading(on) {
		this.calculating = on;
		const btn = $('#cb-btn-calc');
		btn.prop('disabled', on).text(on ? 'Calculando...' : 'Calcular plan de corte');
	}

	_show_error(msg) {
		$('#cb-error').text(msg).show();
	}

	_hide_error() {
		$('#cb-error').hide();
	}
}
