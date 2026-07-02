frappe.pages['admin-patrones'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Administrar Patrones',
		single_column: true,
	});
	$(frappe.render_template('admin_patrones', {})).appendTo(page.body);
	page.set_primary_action(__('Vectorizar imagen'), () => {
		frappe.set_route('vectorizar-patron');
	}, 'camera');
	page.set_secondary_action(__('Ir al Panel Decorativo'), () => {
		frappe.set_route('panel-decorativo');
	});
	new AdminPatrones(page);
};

class AdminPatrones {
	constructor(page) {
		this.page = page;
		this.file_url = null;      // /private/files/xxx.dxf tras FileUploader
		this.file_label = null;

		this.make_customer_control();
		this.bind_events();
		this.load_list();
	}

	// ------------------------------------------------------------------
	// Cliente (solo visible si Exclusivo)
	// ------------------------------------------------------------------

	make_customer_control() {
		this.customer_control = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Link',
				options: 'Customer',
				fieldname: 'cliente',
				placeholder: __('Cliente'),
			},
			parent: $('#ap-customer-field'),
			render_input: true,
		});
	}

	get_customer() {
		return (this.customer_control && this.customer_control.get_value()) || '';
	}

	// ------------------------------------------------------------------
	// Eventos
	// ------------------------------------------------------------------

	bind_events() {
		$('#ap-visibilidad').on('change', () => {
			const excl = $('#ap-visibilidad').val() === 'Exclusivo';
			$('#ap-customer-group').toggleClass('hidden', !excl);
		});
		$('#ap-file-drop').on('click', () => this.pick_file());
		$('#ap-btn-subir').on('click', () => this.subir());
	}

	// ------------------------------------------------------------------
	// Selección de archivo — FileUploader nativo de Frappe (privado)
	// ------------------------------------------------------------------

	pick_file() {
		new frappe.ui.FileUploader({
			as_dataurl: false,
			allow_multiple: false,
			restrictions: { allowed_file_types: ['.dxf'] },
			make_attachments_public: false,
			on_success: (file_doc) => {
				this.file_url = file_doc.file_url;
				this.file_label = file_doc.file_name || file_doc.file_url;
				$('#ap-file-prompt').addClass('hidden');
				$('#ap-file-name').removeClass('hidden').text('✓ ' + this.file_label);
				$('#ap-file-drop').addClass('has-file');
				// Sugerir nombre desde el archivo si el campo está vacío
				if (!$('#ap-nombre').val() && file_doc.file_name) {
					$('#ap-nombre').val(file_doc.file_name.replace(/\.dxf$/i, ''));
				}
			},
		});
	}

	// ------------------------------------------------------------------
	// Subir
	// ------------------------------------------------------------------

	subir() {
		const status = $('#ap-status').css('color', '').text('');
		const nombre = $('#ap-nombre').val().trim();
		const stepx = parseFloat($('#ap-stepx').val());
		const stepy = parseFloat($('#ap-stepy').val());
		const visibilidad = $('#ap-visibilidad').val();
		const customer = this.get_customer();

		const fail = (msg) => status.css('color', 'var(--si-red)').text(msg);
		if (!nombre) return fail(__('Falta el nombre.'));
		if (!(stepx > 0)) return fail(__('Paso X inválido.'));
		if (!(stepy > 0)) return fail(__('Paso Y inválido.'));
		if (!this.file_url) return fail(__('Elegí un archivo DXF.'));
		if (visibilidad === 'Exclusivo' && !customer)
			return fail(__('Elegí el cliente para un patrón exclusivo.'));

		const args = {
			nombre: nombre,
			step_x: stepx,
			step_y: stepy,
			visibilidad: visibilidad === 'Publico' ? 'Público' : 'Exclusivo',
			file_url: this.file_url,
			customer: visibilidad === 'Exclusivo' ? customer : null,
		};

		status.css('color', '').text(__('Subiendo…'));
		const btn = $('#ap-btn-subir').prop('disabled', true);

		// Degradación: si el endpoint aún no existe (backend de Punto pendiente),
		// no rompemos — el archivo ya quedó subido como File; avisamos y seguimos.
		frappe.call({
			method: 'sistema_industrial.api.patrones.upload_pattern',
			args: args,
			callback: (r) => {
				const m = r.message || {};
				if (m.ok) {
					status.css('color', 'var(--si-green)')
						.text(__('✓ Patrón guardado: ') + m.name + ' (v' + (m.version || 1) + ')');
					this.reset_form();
					this.load_list();
					// Si el DXF trae splines, ofrecer conversión a arcos (no bloqueante).
					if (m.has_splines) this.offer_convert(m.name, m.spline_count || 0);
				} else {
					fail(__('Error: ') + (m.error || __('desconocido')));
				}
			},
			error: (e) => {
				const httpish = e && (e.httpStatus || (e.exc_type || '') + '');
				if (String(httpish).includes('404') || /does not exist|not found|AttributeError/i.test(JSON.stringify(e || {}))) {
					status.css('color', 'var(--si-accent2)')
						.text(__('Archivo subido. El backend de registro (upload_pattern) todavía no está publicado — se conectará cuando Punto lo despliegue.'));
				} else {
					fail(__('Error al subir. Revisá la consola.'));
				}
			},
			always: () => btn.prop('disabled', false),
		});
	}

	reset_form() {
		$('#ap-nombre').val('');
		$('#ap-stepx').val('');
		$('#ap-stepy').val('');
		$('#ap-file-prompt').removeClass('hidden');
		$('#ap-file-name').addClass('hidden').text('');
		$('#ap-file-drop').removeClass('has-file');
		this.file_url = null;
		this.file_label = null;
	}

	// ------------------------------------------------------------------
	// Listado — list_admin (todos + cliente + activo); fallback a get_all
	// ------------------------------------------------------------------

	load_list() {
		// Intento el endpoint admin vía fetch directo para que un 404 pre-endpoint
		// no dispare el diálogo de error de Frappe.
		fetch('/api/method/sistema_industrial.api.patrones.list_admin', {
			headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
		})
			.then((r) => (r.ok ? r.json() : null))
			.then((d) => {
				const rows = d && d.message && d.message.rows;
				if (rows) {
					this.render_grid(rows, true);
				} else {
					this.load_list_fallback();
				}
			})
			.catch(() => this.load_list_fallback());
	}

	load_list_fallback() {
		// get_all existe hoy: muestra públicos (sin inactivos ni cliente). Suficiente
		// para ver la galería mientras list_admin no esté.
		frappe.call({
			method: 'sistema_industrial.api.patrones.get_all',
			callback: (r) => this.render_grid(((r.message || {}).rows) || [], false),
			error: () => this.render_grid([], false),
		});
	}

	render_grid(rows, admin_mode) {
		const grid = $('#ap-grid').empty();
		if (!rows.length) {
			grid.append($('<div class="ap-empty">').text(__('No hay patrones cargados todavía.')));
			return;
		}
		rows.forEach((p) => {
			const activo = admin_mode ? p.activo !== 0 : true;
			const card = $('<div class="ap-card">').toggleClass('inactivo', !activo);

			if (p.thumbnail_url) {
				card.append($('<img class="ap-thumb" loading="lazy">').attr('src', p.thumbnail_url));
			} else {
				card.append(
					$('<svg class="ap-thumb-svg" viewBox="0 0 130 100"><rect x="10" y="10" width="110" height="80" fill="none" stroke="#c5dde8" stroke-width="2"/></svg>')
				);
			}

			card.append($('<div class="ap-card-name">').text(p.label || p.name));

			const badges = $('<div class="ap-badges">');
			const excl = p.visibilidad === 'Exclusivo';
			badges.append(
				$('<span class="ap-badge">')
					.addClass(excl ? 'ap-badge-exclusivo' : 'ap-badge-generico')
					.text(excl ? __('Exclusivo') : __('Genérico'))
			);
			if (!p.file_available)
				badges.append($('<span class="ap-badge ap-badge-nodisp">').text(__('No disp.')));
			if (p.has_splines)
				badges.append($('<span class="ap-badge ap-badge-splines">').text(__('⚠ splines')));
			if (!activo)
				badges.append($('<span class="ap-badge ap-badge-baja">').text(__('Baja')));
			card.append(badges);

			if (excl && p.cliente)
				card.append($('<div class="ap-card-cliente">').text(p.cliente));

			// Convertir splines a arcos — solo cuando el patrón las tiene y está activo
			if (activo && p.has_splines) {
				card.append(
					$('<button class="btn btn-xs btn-default ap-convert">')
						.text(__('Convertir a arcos'))
						.on('click', () => this.convertir(p.name, p.spline_count || 0))
				);
			}

			// Borrar (baja lógica) — solo para activos
			if (activo) {
				card.append(
					$('<button class="btn btn-xs btn-default ap-del" title="Dar de baja">✕</button>')
						.on('click', () => this.borrar(p.name))
				);
			}

			grid.append(card);
		});
	}

	// ------------------------------------------------------------------
	// Baja lógica
	// ------------------------------------------------------------------

	borrar(name) {
		frappe.confirm(
			__('¿Dar de baja el patrón "{0}"? El archivo DXF se conserva; solo deja de ofrecerse.', [name]),
			() => {
				frappe.call({
					method: 'sistema_industrial.api.patrones.delete_pattern',
					args: { name: name },
					callback: (r) => {
						const m = r.message || {};
						if (m.ok) {
							frappe.show_alert({ message: __('Patrón dado de baja'), indicator: 'orange' });
							this.load_list();
						} else {
							frappe.msgprint(__('No se pudo dar de baja: ') + (m.error || ''));
						}
					},
					error: () => frappe.msgprint(__('El backend de baja (delete_pattern) todavía no está publicado.')),
				});
			}
		);
	}

	// ------------------------------------------------------------------
	// Splines → arcos
	// ------------------------------------------------------------------

	// Diálogo no bloqueante tras un upload que trajo splines.
	offer_convert(name, count) {
		const msg = count
			? __('Este patrón contiene {0} splines. El láser trabaja mejor con arcos — ¿convertir ahora?', [count])
			: __('Este patrón contiene splines. El láser trabaja mejor con arcos — ¿convertir ahora?');
		frappe.confirm(
			msg,
			() => this.convertir(name, count),      // Convertir a arcos
			() => {}                                  // Dejar como está (no-op)
		);
	}

	// Llama al backend de conversión; reusable desde el diálogo y desde la card.
	convertir(name, count) {
		frappe.call({
			method: 'sistema_industrial.api.patrones.convert_splines',
			args: { name: name },
			freeze: true,
			freeze_message: __('Convirtiendo splines a arcos…'),
			callback: (r) => {
				const m = r.message || {};
				if (m.ok) {
					const partes = [];
					if (m.splines_converted != null) partes.push(m.splines_converted + ' ' + __('splines'));
					const productos = [];
					if (m.arcs_created != null) productos.push(m.arcs_created + ' ' + __('arcos'));
					if (m.lines_created != null) productos.push(m.lines_created + ' ' + __('líneas'));
					let txt = __('Conversión lista');
					if (partes.length && productos.length)
						txt = __('{0} convertidas en {1}', [partes.join(''), productos.join(' y ')]);
					if (m.version != null) txt += ' — v' + m.version;
					frappe.show_alert({ message: '✓ ' + txt, indicator: 'green' });
					this.load_list();
				} else {
					frappe.msgprint(__('No se pudo convertir: ') + (m.error || __('desconocido')));
				}
			},
			error: (e) => {
				// Degradación: convert_splines todavía no publicado (PUNTO_TASK_056).
				const blob = JSON.stringify(e || {});
				if (/does not exist|not found|AttributeError|404/i.test(blob)) {
					frappe.msgprint(
						__('El backend de conversión (convert_splines) todavía no está publicado. Se conectará cuando Punto lo despliegue.')
					);
				} else {
					frappe.msgprint(__('Error al convertir. Revisá la consola.'));
				}
			},
		});
	}
}
