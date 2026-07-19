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
// El precio se carga POR FAMILIA y se propaga a todos sus espesores
// (definición de Constantino 2026-07-14).
const PR_FAMILIAS = [
	{ key: 'hierro', label: 'Doble decapada' },
	{ key: 'galvanizada', label: 'Galvanizado' },
	{ key: 'inox430', label: 'Inoxidable 430' },
	{ key: 'inox304', label: 'Inoxidable 304' },
];

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
		])
			.then(([precios, mats]) => {
				precios = precios || {};
				mats = mats || {};
				this.rows = (mats.rows || []).filter((r) => r && r.familia);
				this.source = mats.source || '';

				$('#pr-segundo-laser').val(precios.precio_segundo_laser || 0);
				$('#pr-por-plegado').val(precios.precio_por_plegado || 0);

				this.render_familias();
				this.snapshot();
				this.status('', '');
			})
			.catch(() => this.status(__('No se pudieron cargar los precios. Revisá la consola.'), 'var(--si-red)'));
	}

	// Valor representativo de una familia + si sus filas divergen entre sí.
	// (La migración les puso el mismo precio a todas; si alguien editó una fila
	// suelta por el Desk, avisamos que guardar las va a unificar.)
	familia_info(key, field) {
		const rows = this.rows.filter((r) => r.familia === key);
		const vals = rows.map((r) => Number(r[field] || 0));
		const uniq = Array.from(new Set(vals));
		return { rows: rows, count: rows.length, valor: vals.length ? vals[0] : 0, diverge: uniq.length > 1, valores: uniq };
	}

	render_familias() {
		const tbody = $('#pr-familias-tbody').empty();
		const avisos = [];

		PR_FAMILIAS.forEach((fam) => {
			const kg = this.familia_info(fam.key, 'precio_por_kg');
			const pkg = this.familia_info(fam.key, 'precio_plegar_por_kg');

			const tr = $('<tr>');
			const $lbl = $('<td>').text(fam.label);
			$lbl.append(
				$('<div class="dimmed pr-hint">').text(
					kg.count
						? __('{0} espesores', [kg.count])
						: __('sin materiales cargados')
				)
			);
			tr.append($lbl);

			[['precio_por_kg', kg], ['precio_plegar_por_kg', pkg]].forEach(([field, info]) => {
				const inp = $('<input type="number" min="0" step="0.01" class="pr-input">')
					.attr('data-familia', fam.key)
					.attr('data-field', field)
					.val(info.valor);
				if (!info.count) inp.prop('disabled', true);
				tr.append($('<td style="text-align:right">').append(inp));
				if (info.diverge) {
					avisos.push(
						__('{0} — "{1}": los espesores no tienen todos el mismo valor ({2}). Al guardar se unifican.', [
							fam.label,
							field === 'precio_por_kg' ? __('Precio por kg') : __('Precio de plegado por kg'),
							info.valores.join(' / '),
						])
					);
				}
			});

			tbody.append(tr);
		});

		// Familias presentes en la base que no están en la lista de arriba: se
		// avisan en vez de quedar invisibles (no se editan desde acá).
		const conocidas = PR_FAMILIAS.map((f) => f.key);
		const otras = Array.from(new Set(this.rows.map((r) => r.familia).filter((f) => conocidas.indexOf(f) === -1)));
		if (otras.length)
			avisos.push(__('Hay materiales de otras familias que no se editan desde esta pantalla: {0}', [otras.join(', ')]));

		if (this.source && this.source !== 'frappe')
			avisos.push(
				__('Los materiales se están leyendo del archivo legacy, no de la base — los precios por familia no se pueden guardar hasta migrarlos.')
			);

		const $div = $('#pr-divergencia').empty();
		avisos.forEach((a) => $div.append($('<div class="error-box" style="margin-top:8px">').text(a)));
	}

	// ------------------------------------------------------------------
	// Guardar
	// ------------------------------------------------------------------

	snapshot() {
		const fam = {};
		PR_FAMILIAS.forEach((f) => {
			fam[f.key] = {
				precio_por_kg: this.input_val(f.key, 'precio_por_kg'),
				precio_plegar_por_kg: this.input_val(f.key, 'precio_plegar_por_kg'),
			};
		});
		this.loaded = {
			precio_segundo_laser: parseFloat($('#pr-segundo-laser').val()) || 0,
			precio_por_plegado: parseFloat($('#pr-por-plegado').val()) || 0,
			fam: fam,
		};
	}

	input_val(famKey, field) {
		const $i = $('.pr-input[data-familia="' + famKey + '"][data-field="' + field + '"]');
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
			const kg = this.input_val(fam.key, 'precio_por_kg');
			const pkg = this.input_val(fam.key, 'precio_plegar_por_kg');
			const prev = this.loaded.fam[fam.key] || {};
			if (kg === prev.precio_por_kg && pkg === prev.precio_plegar_por_kg) continue;
			if (!(kg >= 0) || !(pkg >= 0))
				return this.status(__('Precio inválido en {0}.', [fam.label]), 'var(--si-red)');
			const filas = this.rows.filter((r) => r.familia === fam.key && r.name);
			if (!filas.length)
				return this.status(__('No hay materiales en la base para {0}.', [fam.label]), 'var(--si-red)');
			cambios_familia.push({ fam: fam, kg: kg, pkg: pkg, filas: filas });
		}

		if (cambios_familia.length && this.source !== 'frappe')
			return this.status(
				__('Los precios por familia no se pueden guardar: los materiales no están en la base todavía.'),
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

		// Por familia: el precio se propaga a todas sus filas activas. Solo se
		// tocan las familias cuyo valor cambió (evita 28 llamadas al pedo).
		cambios_familia.forEach((c) => {
			c.filas.forEach((r) => {
				n_filas++;
				ops.push(
					this.call('sistema_industrial.api.materiales.update', {
						name: r.name,
						data: JSON.stringify({ precio_por_kg: c.kg, precio_plegar_por_kg: c.pkg }),
					})
				);
			});
		});

		const btn = $('#pr-btn-guardar').prop('disabled', true);
		this.status(__('Guardando…'), '');
		Promise.all(ops)
			.then(() => {
				frappe.show_alert({ message: __('Precios guardados'), indicator: 'green' });
				// Releer de la base ANTES de confirmar: lo que se muestra es lo que
				// realmente quedó grabado (load() reescribe el status, por eso el
				// mensaje de éxito va después).
				return this.load();
			})
			.then(() => {
				const detalle = n_filas ? __(' ({0} materiales actualizados)', [n_filas]) : '';
				this.status('✓ ' + __('Precios guardados') + detalle, 'var(--si-green)');
			})
			.catch(() => this.status(__('Error al guardar. Revisá la consola.'), 'var(--si-red)'))
			.then(() => btn.prop('disabled', false));
	}
}
