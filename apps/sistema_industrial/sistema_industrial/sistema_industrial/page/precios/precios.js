frappe.pages['precios'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Precios',
		single_column: true,
	});
	$(frappe.render_template('precios', {})).appendTo(page.body);
	page.set_secondary_action(__('Ir al Panel Decorativo'), () => {
		frappe.set_route('panel-decorativo');
	});
	new Precios(page);
};

// Familias de material: valor real en SI Material Corte.familia -> etiqueta que
// usaba la pantalla vieja de precios diarios (render_precios del standalone).
const PR_FAMILIAS = [
	{ key: 'hierro', label: 'Doble decapada' },
	{ key: 'galvanizada', label: 'Galvanizado' },
	{ key: 'inox430', label: 'Inoxidable 430' },
	{ key: 'inox304', label: 'Inoxidable 304' },
];

// Canon (Brújula / docs/04_PRICING_EXCEL_TANGO.md): TANGO ES EL MAESTRO DE
// PRECIOS PUBLICADOS; ERPNext guarda una copia. Por eso esta página NO escribe
// precios de venta (precio_por_kg): hacerlo crearía una segunda fuente de verdad
// y desincronizaría el sistema de la facturación real en silencio.
// Sí edita los parámetros de COSTEO, que son propios del sistema.
const PR_CAMPO_VENTA = 'precio_por_kg';           // solo lectura (maestro: Tango)
const PR_CAMPO_COSTEO = 'precio_plegar_por_kg';   // editable (nuestro)

class Precios {
	constructor(page) {
		this.page = page;
		this.rows = [];          // filas activas de SI Material Corte
		this.source = '';        // "frappe" | "legacy_json" | "empty"
		this.loaded = null;      // snapshot de lo cargado (para detectar cambios)
		this.bind_events();
		this.load();
	}

	// Promesa sobre frappe.call — evita anidar callbacks al combinar llamadas.
	call(method, args) {
		return new Promise((resolve, reject) => {
			frappe.call({ method: method, args: args || {}, callback: (r) => resolve(r.message), error: reject });
		});
	}

	bind_events() {
		$('#pr-btn-guardar').on('click', () => this.guardar());
		$('#pr-btn-recargar').on('click', () => this.load());
	}

	status(msg, color) {
		$('#pr-status').css('color', color || '').text(msg || '');
	}

	// ------------------------------------------------------------------
	// Carga
	// ------------------------------------------------------------------

	load() {
		this.status(__('Cargando…'), '');
		return Promise.all([
			this.call('sistema_industrial.api.materiales.get_precios'),
			this.call('sistema_industrial.api.materiales.get_all'),
			this.ultima_actualizacion(),
		])
			.then(([precios, mats, ultima]) => {
				precios = precios || {};
				mats = mats || {};
				this.rows = (mats.rows || []).filter((r) => r && r.familia);
				this.source = mats.source || '';

				$('#pr-segundo-laser').val(precios.precio_segundo_laser || 0);
				$('#pr-por-plegado').val(precios.precio_por_plegado || 0);

				this.render_costeo();
				this.render_venta();
				this.render_sync(ultima);
				this.render_avisos();
				this.snapshot();
				this.status('', '');
			})
			.catch(() => this.status(__('No se pudieron cargar los precios. Revisá la consola.'), 'var(--si-red)'));
	}

	// Fecha del último cambio del dato en ERPNext. NO es una fecha de
	// sincronización con Tango — hoy no existe ese sync (ver render_sync).
	ultima_actualizacion() {
		return this.call('frappe.client.get_list', {
			doctype: 'SI Material Corte',
			filters: { activo: 1 },
			fields: ['modified'],
			order_by: 'modified desc',
			limit_page_length: 1,
		})
			.then((r) => (r && r.length ? r[0].modified : null))
			.catch(() => null);
	}

	// Valor representativo de una familia + si sus filas divergen entre sí.
	familia_info(key, field) {
		const rows = this.rows.filter((r) => r.familia === key);
		const vals = rows.map((r) => Number(r[field] || 0));
		const uniq = Array.from(new Set(vals));
		return { rows: rows, count: rows.length, valor: vals.length ? vals[0] : 0, diverge: uniq.length > 1, valores: uniq };
	}

	// --- Costeo: editable ---
	render_costeo() {
		const tbody = $('#pr-costeo-tbody').empty();
		PR_FAMILIAS.forEach((fam) => {
			const info = this.familia_info(fam.key, PR_CAMPO_COSTEO);
			const tr = $('<tr>');
			const $lbl = $('<td>').text(fam.label);
			$lbl.append(
				$('<div class="dimmed pr-hint">').text(
					info.count ? __('{0} espesores', [info.count]) : __('sin materiales cargados')
				)
			);
			tr.append($lbl);

			const inp = $('<input type="number" min="0" step="0.01" class="pr-input">')
				.attr('data-familia', fam.key)
				.val(info.valor);
			if (!info.count) inp.prop('disabled', true);
			tr.append($('<td style="text-align:right">').append(inp));
			tbody.append(tr);
		});
	}

	// --- Venta: SOLO LECTURA (maestro Tango) ---
	render_venta() {
		const tbody = $('#pr-venta-tbody').empty();
		PR_FAMILIAS.forEach((fam) => {
			const info = this.familia_info(fam.key, PR_CAMPO_VENTA);
			const tr = $('<tr>');
			const $lbl = $('<td>').text(fam.label);
			$lbl.append(
				$('<div class="dimmed pr-hint">').text(
					info.count ? __('{0} espesores', [info.count]) : __('sin materiales cargados')
				)
			);
			tr.append($lbl);
			tr.append(
				$('<td style="text-align:right" class="pr-readonly">').text(
					info.count ? format_currency(info.valor, 'ARS') : '—'
				)
			);
			tbody.append(tr);
		});
	}

	// Procedencia del precio de venta. Un precio en pantalla sin fecha engaña
	// al que lo lee, así que se dice explícitamente qué se sabe y qué no.
	render_sync(ultima) {
		const $d = $('#pr-sync-info').empty();
		const fecha = ultima
			? frappe.datetime.str_to_user(ultima)
			: null;
		$d.append(
			$('<div>').html(
				'<b>' + __('Sincronización desde Tango') + ':</b> ' +
					__('no implementada todavía — estos valores son los de la carga inicial y no se actualizan solos.')
			)
		);
		$d.append(
			$('<div class="dimmed">').text(
				fecha
					? __('Último cambio del dato en ERPNext: {0}', [fecha])
					: __('Sin fecha de última actualización disponible.')
			)
		);
	}

	render_avisos() {
		const avisos = [];
		PR_FAMILIAS.forEach((fam) => {
			[[PR_CAMPO_VENTA, __('Precio por kg')], [PR_CAMPO_COSTEO, __('Precio de plegado por kg')]].forEach(
				([field, label]) => {
					const info = this.familia_info(fam.key, field);
					if (info.diverge)
						avisos.push(
							__('{0} — "{1}": los espesores no tienen todos el mismo valor ({2}).', [
								fam.label,
								label,
								info.valores.join(' / '),
							])
						);
				}
			);
		});

		const conocidas = PR_FAMILIAS.map((f) => f.key);
		const otras = Array.from(new Set(this.rows.map((r) => r.familia).filter((f) => conocidas.indexOf(f) === -1)));
		if (otras.length)
			avisos.push(__('Hay materiales de otras familias que no se muestran en esta pantalla: {0}', [otras.join(', ')]));

		if (this.source && this.source !== 'frappe')
			avisos.push(__('Los materiales se están leyendo del archivo legacy, no de la base.'));

		const $div = $('#pr-avisos').empty();
		avisos.forEach((a) => $div.append($('<div class="error-box" style="margin-top:8px">').text(a)));
	}

	// ------------------------------------------------------------------
	// Guardar — SOLO parámetros de costeo
	// ------------------------------------------------------------------

	snapshot() {
		const fam = {};
		PR_FAMILIAS.forEach((f) => {
			fam[f.key] = this.input_val(f.key);
		});
		this.loaded = {
			precio_segundo_laser: parseFloat($('#pr-segundo-laser').val()) || 0,
			precio_por_plegado: parseFloat($('#pr-por-plegado').val()) || 0,
			fam: fam,
		};
	}

	input_val(famKey) {
		const $i = $('.pr-input[data-familia="' + famKey + '"]');
		return $i.length ? parseFloat($i.val()) || 0 : 0;
	}

	guardar() {
		if (!this.loaded) return;

		const seg = parseFloat($('#pr-segundo-laser').val());
		const pleg = parseFloat($('#pr-por-plegado').val());
		if (!(seg >= 0)) return this.status(__('Precio por segundo de láser inválido.'), 'var(--si-red)');
		if (!(pleg >= 0)) return this.status(__('Precio por plegado inválido.'), 'var(--si-red)');

		// --- Paso 1: juntar cambios y VALIDAR TODO antes de disparar nada ---
		// this.call() dispara el request al construirse, así que no se puede
		// validar a mitad del recorrido: quedaría un guardado parcial reportado
		// como éxito (ej. familia 1 grabada y familia 2 inválida).
		const cambios_familia = [];
		for (const fam of PR_FAMILIAS) {
			const val = this.input_val(fam.key);
			if (val === this.loaded.fam[fam.key]) continue;
			if (!(val >= 0))
				return this.status(__('Precio de plegado por kg inválido en {0}.', [fam.label]), 'var(--si-red)');
			const filas = this.rows.filter((r) => r.familia === fam.key && r.name);
			if (!filas.length)
				return this.status(__('No hay materiales en la base para {0}.', [fam.label]), 'var(--si-red)');
			cambios_familia.push({ fam: fam, val: val, filas: filas });
		}

		if (cambios_familia.length && this.source !== 'frappe')
			return this.status(
				__('No se puede guardar: los materiales no están en la base todavía.'),
				'var(--si-red)'
			);

		const globales_cambiaron =
			seg !== this.loaded.precio_segundo_laser || pleg !== this.loaded.precio_por_plegado;
		if (!globales_cambiaron && !cambios_familia.length)
			return this.status(__('No hay cambios para guardar.'), 'var(--si-muted)');

		// --- Paso 2: recién acá se disparan los requests ---
		const ops = [];
		let n_filas = 0;

		if (globales_cambiaron) {
			ops.push(
				this.call('sistema_industrial.api.materiales.save_precios', {
					data: JSON.stringify({ precio_segundo_laser: seg, precio_por_plegado: pleg }),
				})
			);
		}

		cambios_familia.forEach((c) => {
			c.filas.forEach((r) => {
				n_filas++;
				// SOLO el campo de costeo. Nunca se manda precio_por_kg: es el
				// precio de venta y su maestro es Tango (mandarlo lo pisaría).
				const data = {};
				data[PR_CAMPO_COSTEO] = c.val;
				ops.push(
					this.call('sistema_industrial.api.materiales.update', {
						name: r.name,
						data: JSON.stringify(data),
					})
				);
			});
		});

		const btn = $('#pr-btn-guardar').prop('disabled', true);
		this.status(__('Guardando…'), '');
		Promise.all(ops)
			.then(() => {
				frappe.show_alert({ message: __('Parámetros de costeo guardados'), indicator: 'green' });
				// Releer de la base ANTES de confirmar: lo que se muestra es lo que
				// realmente quedó grabado (load() reescribe el status, por eso el
				// mensaje de éxito va después).
				return this.load();
			})
			.then(() => {
				const detalle = n_filas ? __(' ({0} materiales actualizados)', [n_filas]) : '';
				this.status('✓ ' + __('Parámetros de costeo guardados') + detalle, 'var(--si-green)');
			})
			.catch(() => this.status(__('Error al guardar. Revisá la consola.'), 'var(--si-red)'))
			.then(() => btn.prop('disabled', false));
	}
}
