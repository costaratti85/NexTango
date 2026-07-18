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

	// Galería con thumbnails, agrupada en dos secciones (Motor nativo / DXF y
	// Cargados) — igual criterio que panel_decorativo.js. Los thumbnails vienen
	// de get_all()/list_admin() (Punto, thumbnails de panel tileado v3, commit
	// 8a8adc5); si no hay PNG generado todavía, placeholder de contorno.
	render_grid(rows, admin_mode) {
		const grid = $('#ap-grid').empty();
		if (!rows.length) {
			grid.append($('<div class="ap-empty">').text(__('No hay patrones cargados todavía.')));
			return;
		}

		const build_card = (p) => {
			const activo = admin_mode ? p.activo !== 0 : true;
			const card = $('<div class="ap-card">').toggleClass('inactivo', !activo);

			if (p.thumbnail_url) {
				card.append($('<img class="ap-thumb" loading="lazy">').attr('src', p.thumbnail_url).attr('alt', p.label || p.name));
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

			// Actualizar (editar definición / subir o reapuntar DXF) — solo cargados
			// (Archivo/Vectorizado). Incluye los "No disp.": el caso de uso principal
			// es justamente corregir la ruta de esos (VEGA_UI_ACTUALIZAR_PATRON).
			if (activo && p.tipo !== 'Paramétrico') {
				card.append(
					$('<button class="btn btn-xs btn-default ap-edit" title="Actualizar patrón">✎</button>')
						.on('click', () => this.open_edit_dialog(p))
				);
			}

			return card;
		};

		const append_section = (title, list) => {
			if (!list.length) return;
			grid.append($('<div class="ap-section-title">').text(title));
			const row = $('<div class="ap-section-row">');
			list.forEach((p) => row.append(build_card(p)));
			grid.append(row);
		};

		const nativos = rows.filter((p) => p.tipo === 'Paramétrico');
		const cargados = rows.filter((p) => p.tipo === 'Archivo' || p.tipo === 'Vectorizado');
		const otros = rows.filter((p) => p.tipo !== 'Paramétrico' && p.tipo !== 'Archivo' && p.tipo !== 'Vectorizado');

		append_section(__('Motor nativo'), nativos);
		append_section(__('DXF / Cargados'), cargados);
		append_section(__('Otros'), otros);
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
	// Actualizar patrón — editar definición y subir/reapuntar el DXF
	// (VEGA_UI_ACTUALIZAR_PATRON; backend de Atlas: update_pattern.
	// El contrato exacto puede ajustarse cuando Atlas lo publique — la llamada
	// está aislada en call_update_pattern()).
	// ------------------------------------------------------------------

	open_edit_dialog(p) {
		// Datos frescos: descripcion no viene en list_admin; get_patron sí la trae
		// (más archivo_dxf_url y parametros vigentes). Fallback: datos de la fila.
		frappe.call({
			method: 'sistema_industrial.api.patrones.get_patron',
			args: { name: p.name },
			callback: (r) => this.show_edit_dialog(p, r.message || {}),
			error: () => this.show_edit_dialog(p, {}),
		});
	}

	show_edit_dialog(p, det) {
		const params = det.parametros || p.parametros || {};
		const cur = {
			version: det.version != null ? det.version : p.version,
			step_x: params.step_x != null ? params.step_x : p.step_x,
			step_y: params.step_y != null ? params.step_y : p.step_y,
			visibilidad: det.visibilidad || p.visibilidad || 'Público',
			cliente: p.cliente || '',
			descripcion: det.descripcion || '',
			file_path: det.archivo_dxf_url || p.file_path || '',
			file_available: det.file_available != null ? det.file_available : p.file_available,
		};
		this._edit_file_url = null;
		this._edit_file_label = null;

		const disp = cur.file_available
			? '<span style="color:var(--si-green);font-weight:600">' + __('disponible') + '</span>'
			: '<span style="color:var(--si-red);font-weight:600">' + __('NO disponible') + '</span>';

		const d = new frappe.ui.Dialog({
			title: __('Actualizar patrón: {0}', [p.name]),
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'info',
					options:
						'<div style="font-size:12px;color:var(--si-muted);margin-bottom:4px">' +
						__('Versión actual') + ': <b>v' + (cur.version || 1) + '</b> — ' +
						__('guardar crea una versión nueva; las anteriores quedan congeladas (contrato SI Patron Version).') +
						'</div>',
				},
				// Las TRES cosas actualizables (pedido de Constantino 2026-07-14):
				// archivo DXF + offset X + offset Y — van primero y con su vocabulario.
				// "Offset" = paso de tileo del patrón (en la base es parametros.step_x/y;
				// hoy está encodeado en nombres como subte_Offx84_Offy84.dxf).
				{
					fieldtype: 'Float',
					fieldname: 'step_x',
					label: __('Offset X mm'),
					default: cur.step_x,
					description: __('Paso de tileo horizontal (el Offx del nombre del archivo).'),
				},
				{ fieldtype: 'Column Break' },
				{
					fieldtype: 'Float',
					fieldname: 'step_y',
					label: __('Offset Y mm'),
					default: cur.step_y,
					description: __('Paso de tileo vertical (el Offy del nombre del archivo).'),
				},
				{ fieldtype: 'Section Break', label: __('Archivo DXF') },
				{
					fieldtype: 'HTML',
					fieldname: 'file_actual',
					options:
						'<div style="font-size:12px;margin-bottom:6px">' + __('Actual') + ': ' +
						'<code style="word-break:break-all">' +
						frappe.utils.escape_html(cur.file_path || __('(sin archivo)')) +
						'</code> — ' + disp + '</div>',
				},
				{
					fieldtype: 'Data',
					fieldname: 'archivo_dxf',
					label: __('Ruta en el servidor (reapuntar)'),
					default: cur.file_path,
					description: __('Si el archivo en disco tiene otro nombre, corregí acá la ruta. Se valida contra el disco al guardar.'),
				},
				{ fieldtype: 'HTML', fieldname: 'upload_zone' },
				{ fieldtype: 'Section Break', label: __('Definición') },
				{
					fieldtype: 'Select',
					fieldname: 'visibilidad',
					label: __('Visibilidad'),
					options: ['Público', 'Exclusivo'],
					default: cur.visibilidad === 'Exclusivo' ? 'Exclusivo' : 'Público',
				},
				{
					fieldtype: 'Link',
					fieldname: 'customer',
					label: __('Cliente'),
					options: 'Customer',
					default: cur.cliente,
					depends_on: "eval:doc.visibilidad=='Exclusivo'",
				},
				{ fieldtype: 'Small Text', fieldname: 'descripcion', label: __('Descripción'), default: cur.descripcion },
			],
			primary_action_label: __('Guardar cambios'),
			primary_action: (values) => this.guardar_update(p, cur, values, d),
		});

		// Subir un DXF nuevo desde el diálogo (FileUploader nativo, privado) —
		// alternativa al reapuntado: si se sube archivo, reemplaza a la ruta.
		const $zone = $(
			'<div style="margin-top:4px">' +
				'<button class="btn btn-sm btn-default" type="button">⤒ ' + __('Subir DXF nuevo…') + '</button>' +
				'<span class="ap-file-name" style="margin-left:8px"></span>' +
				'<div style="font-size:11px;color:var(--si-muted);margin-top:4px">' +
				__('Si subís un archivo nuevo, tiene prioridad sobre la ruta de arriba.') +
				'</div>' +
			'</div>'
		);
		$zone.find('button').on('click', () => {
			new frappe.ui.FileUploader({
				as_dataurl: false,
				allow_multiple: false,
				restrictions: { allowed_file_types: ['.dxf'] },
				make_attachments_public: false,
				on_success: (file_doc) => {
					this._edit_file_url = file_doc.file_url;
					this._edit_file_label = file_doc.file_name || file_doc.file_url;
					$zone.find('.ap-file-name').text('✓ ' + this._edit_file_label);
				},
			});
		});
		d.get_field('upload_zone').$wrapper.append($zone);
		d.show();
	}

	guardar_update(p, cur, values, d) {
		if (!(values.step_x > 0)) return frappe.msgprint(__('Offset X inválido.'));
		if (!(values.step_y > 0)) return frappe.msgprint(__('Offset Y inválido.'));
		if (values.visibilidad === 'Exclusivo' && !values.customer)
			return frappe.msgprint(__('Elegí el cliente para un patrón exclusivo.'));

		const nueva_ruta = (values.archivo_dxf || '').trim();
		const args = {
			name: p.name,
			step_x: values.step_x,
			step_y: values.step_y,
			visibilidad: values.visibilidad,
			customer: values.visibilidad === 'Exclusivo' ? values.customer : null,
			descripcion: values.descripcion || '',
			// Reapuntar: solo se manda si la ruta cambió (vacío = sin cambio).
			archivo_dxf: nueva_ruta && nueva_ruta !== (cur.file_path || '') ? nueva_ruta : null,
			// DXF nuevo subido: tiene prioridad sobre la ruta.
			file_url: this._edit_file_url || null,
		};
		this.call_update_pattern(args, d);
	}

	// Llamada al endpoint de Atlas, AISLADA: si el contrato final difiere
	// (nombre del método o de los args), este es el único lugar a tocar.
	call_update_pattern(args, d) {
		frappe.call({
			method: 'sistema_industrial.api.patrones.update_pattern',
			args: args,
			freeze: true,
			freeze_message: __('Guardando cambios…'),
			callback: (r) => {
				const m = r.message || {};
				if (m.ok) {
					d.hide();
					frappe.show_alert({
						message: __('✓ Patrón actualizado: ') + (m.name || args.name) + ' (v' + (m.version || '?') + ')',
						indicator: 'green',
					});
					this.load_list();
					// Si el DXF nuevo trae splines, ofrecer conversión (mismo flujo que subir).
					if (m.has_splines) this.offer_convert(m.name || args.name, m.spline_count || 0);
				} else {
					frappe.msgprint(__('No se pudo actualizar: ') + (m.error || __('desconocido')));
				}
			},
			error: (e) => {
				// Degradación: update_pattern todavía no publicado (backend de Atlas
				// en curso, ATLAS_BACKEND_ACTUALIZAR_PATRON) — mismo idiom que
				// upload_pattern/convert_splines pre-publicación.
				const blob = JSON.stringify(e || {});
				if (/does not exist|not found|AttributeError|404/i.test(blob)) {
					frappe.msgprint(
						__('El backend de actualización (update_pattern) todavía no está publicado — Atlas lo está construyendo. La UI queda lista para cuando esté.')
					);
				} else {
					frappe.msgprint(__('Error al actualizar. Revisá la consola.'));
				}
			},
		});
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
