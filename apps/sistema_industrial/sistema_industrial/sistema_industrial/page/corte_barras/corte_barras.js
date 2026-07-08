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
				onchange: () => this._on_item_selected(),
			},
			render_input: true,
		});
	}

	_on_item_selected() {
		const item_code = this.item_ctrl.get_value();
		if (!item_code) return;
		frappe.db.get_value('Item', item_code, 'item_name').then(r => {
			if (!r?.message?.item_name) return;
			const { tipo, medida } = this._parse_item_name(r.message.item_name);
			if (tipo) $('#cb-tipo-material').val(tipo);
			if (medida) $('#cb-medida').val(medida);
		});
	}

	_parse_item_name(item_name) {
		// "CAÑO RECT. 80X40X1.5 MM" → {tipo: "CAÑO RECT.", medida: "80X40X1.5"}
		// Split point: primer dígito. Texto antes = tipo, dígitos en adelante = medida.
		const m = item_name.trim().match(/^(.*?)\s*(\d.*)$/);
		if (!m) return { tipo: item_name.trim(), medida: '' };
		const tipo = m[1].trim();
		const medida = m[2].trim().replace(/\s*(MM|M|KG|M2)\s*$/i, '').trim();
		return { tipo, medida };
	}

	// ── Eventos ───────────────────────────────────────────────────────────────

	_bind_events() {
		$('#cb-btn-add').on('click', () => this._add_row());
		$('#cb-pieces-body').on('click', '.cb-del-row', (e) => {
			const rows = $('#cb-pieces-body tr');
			if (rows.length > 1) $(e.currentTarget).closest('tr').remove();
		});
		$('#cb-btn-calc').on('click', () => this._calcular());
		$('#cb-btn-copy').on('click', () => this._copiar());
		$('#cb-angular-toggle').on('change', () => this._toggle_angular());
		this._bind_keyboard_nav();
	}

	_is_angular() {
		return $('#cb-angular-toggle').is(':checked');
	}

	_toggle_angular() {
		const on = this._is_angular();
		$('.cb-ang-col').toggle(on);
	}

	// ── Tabla de piezas ───────────────────────────────────────────────────────

	// focus_col: 'qty' (default para filas creadas por teclado) o 'len' (para
	// el botón "+ Agregar fila", que ya arranca con cantidad=1 precargada).
	_add_row(focus_col) {
		const ang_visible = this._is_angular();
		const ang_style = ang_visible ? '' : 'display:none;';
		const tr = $(`
			<tr>
				<td><input type="number" class="cb-qty" value="1" min="1" step="1"></td>
				<td><input type="number" class="cb-len" min="1" step="1" placeholder="mm"></td>
				<td class="cb-ang-col" style="${ang_style}"><input type="number" class="cb-izq" value="0" min="0" max="60" step="1"></td>
				<td class="cb-ang-col" style="${ang_style}"><input type="number" class="cb-der" value="0" min="0" max="60" step="1"></td>
				<td class="cb-ang-col" style="${ang_style}"><input type="number" class="cb-cara" value="0" min="0" step="1"></td>
				<td class="cb-ang-col" style="${ang_style}">
					<select class="cb-disp">
						<option value="//">//</option>
						<option value="\\">\</option>
						<option value="/\">/\</option>
						<option value="\/">\/</option>
						<option value="X">X</option>
					</select>
				</td>
				<td><button class="cb-del-row cb-ghost-sm">✕</button></td>
			</tr>`);
		$('#cb-pieces-body').append(tr);
		tr.find(focus_col === 'qty' ? '.cb-qty' : '.cb-len').focus();
		return tr;
	}

	// Navegación tipo planilla: flechas para moverse entre celdas, Enter para
	// avanzar (Cant. -> Largo de la misma fila -> Cant. de la fila siguiente),
	// con creación automática de fila al llegar al final (Enter o flecha abajo
	// en la última fila) — la carga de muchas piezas es más rápida sin soltar
	// el teclado para clickear "+ Agregar fila" cada vez.
	_bind_keyboard_nav() {
		$('#cb-pieces-body').on('keydown', '.cb-qty, .cb-len', (e) => {
			const $input = $(e.currentTarget);
			const $td = $input.closest('td');
			const $tr = $td.closest('tr');
			const is_qty = $input.hasClass('cb-qty');
			const at_start = $input[0].selectionStart === 0;
			const at_end = $input[0].selectionStart === $input.val().length;

			const focus_in_row = ($row, col) => {
				const $target = $row.find(col === 'qty' ? '.cb-qty' : '.cb-len');
				$target.focus();
				$target[0].select();
			};

			switch (e.key) {
				case 'ArrowUp': {
					e.preventDefault(); // el navegador incrementa/decrementa un <input type=number>
					const $prev = $tr.prev('tr');
					if ($prev.length) focus_in_row($prev, is_qty ? 'qty' : 'len');
					break;
				}
				case 'ArrowDown': {
					e.preventDefault();
					const $next = $tr.next('tr');
					if ($next.length) {
						focus_in_row($next, is_qty ? 'qty' : 'len');
					}
					// última fila: a diferencia de Enter, flecha abajo NO crea fila
					// nueva sola — solo navega filas existentes.
					break;
				}
				case 'ArrowLeft':
					if (!is_qty && at_start) {
						e.preventDefault();
						focus_in_row($tr, 'qty');
					}
					break;
				case 'ArrowRight':
					if (is_qty && at_end) {
						e.preventDefault();
						focus_in_row($tr, 'len');
					}
					break;
				case 'Enter': {
					e.preventDefault();
					if (is_qty) {
						focus_in_row($tr, 'len');
					} else {
						const $next = $tr.next('tr');
						if ($next.length) {
							focus_in_row($next, 'qty');
						} else {
							const new_tr = this._add_row('qty');
							new_tr.find('.cb-qty')[0].select();
						}
					}
					break;
				}
			}
		});
	}

	_get_cuts() {
		const angular = this._is_angular();
		const cuts = [];
		$('#cb-pieces-body tr').each(function () {
			const qty = parseInt($(this).find('.cb-qty').val(), 10) || 0;
			const len = parseFloat($(this).find('.cb-len').val()) || 0;
			if (qty <= 0 || len <= 0) return;
			if (angular) {
				const izq = parseFloat($(this).find('.cb-izq').val()) || 0;
				const der = parseFloat($(this).find('.cb-der').val()) || 0;
				const cara = parseFloat($(this).find('.cb-cara').val()) || 0;
				const disp = $(this).find('.cb-disp').val() || '//';
				cuts.push([qty, len, izq, der, cara, disp]);
			} else {
				cuts.push([qty, len]);
			}
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

		// Mostrar modo activo cuando falta un precio (precio=0 → ese modo no aplica)
		this._hide_error();
		if (price_per_bar === 0 && price_per_meter === 0) {
			this._show_info('Sin precios cargados: se muestra solo el plan de corte (costo = $0).');
		} else if (price_per_bar === 0) {
			this._show_info('Precio/barra = $0 → modo solo tramos sueltos por metro.');
		} else if (price_per_meter === 0) {
			this._show_info('Precio/metro = $0 → modo solo barras enteras.');
		} else {
			this._hide_info();
		}

		this._set_loading(true);

		const tipo_material = $('#cb-tipo-material').val().trim();
		const medida = $('#cb-medida').val().trim();
		const angular = this._is_angular();

		frappe.call({
			method: 'sistema_industrial.api.corte_barras.calcular',
			args: {
				bar_len,
				cuts_json: JSON.stringify(cuts),
				tipo_material,
				medida,
				price_per_bar,
				price_per_meter,
				kerf_mm,
				angular,
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

	// ── Formato de pieza angular ──────────────────────────────────────────────

	_fmt_pieza(p) {
		// p puede ser un número (recto) o un array [largo, izq, der, cara, disp] (angular)
		if (!Array.isArray(p)) return `${p}`;
		const [largo, izq, der, cara, disp] = p;
		if (izq === 0 && der === 0) return `${largo}`;
		return `${largo} (${izq}${disp}${der})${cara}`;
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
				const chips = p.pieces.map(pc => `<span class="cb-chip">${this._fmt_pieza(pc)}</span>`).join('');
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
			const chips = data.tramo_pieces.map(pc =>
				`<span class="cb-tramo-chip">${this._fmt_pieza(pc)} mm</span>`
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

		// Texto de salida para orden de trabajo
		if (data.texto_salida) {
			$('#cb-texto-salida').val(data.texto_salida);
			$('#cb-texto-card').show();
		} else {
			$('#cb-texto-card').hide();
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

	_show_info(msg) {
		$('#cb-info').text(msg).show();
	}

	_hide_info() {
		$('#cb-info').hide();
	}

	_copiar() {
		const txt = $('#cb-texto-salida').val();
		if (!txt) return;

		const _feedback = () => {
			const btn = $('#cb-btn-copy');
			btn.text('¡Copiado!');
			setTimeout(() => btn.text('Copiar para presupuesto'), 1800);
		};

		// navigator.clipboard requiere HTTPS — en HTTP (servidor local/intranet)
		// falla silenciosamente. Fallback: textarea temporal fuera del viewport.
		if (navigator.clipboard && window.isSecureContext) {
			navigator.clipboard.writeText(txt).then(_feedback).catch(() => this._copiar_fallback(txt, _feedback));
		} else {
			this._copiar_fallback(txt, _feedback);
		}
	}

	_copiar_fallback(txt, callback) {
		const el = document.createElement('textarea');
		el.value = txt;
		el.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
		document.body.appendChild(el);
		el.focus();
		el.select();
		try { document.execCommand('copy'); } catch (_) {}
		document.body.removeChild(el);
		if (callback) callback();
	}
}
