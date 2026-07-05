// Botón "Actualizar" (sync manual Tango → ERPNext) junto a los selectores de
// Customer — compartido entre panel-decorativo, plegados-complejos y
// perfiles-plegados (MSG_023 de Nova). Un solo bloque en vez de repetir la
// lógica en cada page.
//
// CONTRATO PROVISORIO contra Forge (MSG_024, en curso al momento de escribir
// esto — no confirmado):
//   método:    sistema_industrial.api.tango_sync.sync_customers_now
//   respuesta: { ok: true, created: N, updated: N, failed: N }
//           ó: { ok: false, error: "..." }
// Si Forge define un contrato distinto (p.ej. async con job_id), este archivo
// es el ÚNICO lugar que hay que tocar — las 3 pages no conocen el detalle.
frappe.provide('sistema_industrial');

// control: la instancia devuelta por frappe.ui.form.make_control (Link a Customer).
// container_selector: el mismo selector que se usó como `parent` de esa control.
sistema_industrial.attach_customer_sync_button = function (control, container_selector) {
	const $container = $(container_selector);
	$container.addClass('si-customer-sync-row');

	const $btn = $(
		'<button type="button" class="si-customer-sync-btn" title="' +
			__('Actualizar clientes desde Tango') +
			'">\u{1F504}</button>'
	);
	$container.append($btn);

	$btn.on('click', function () {
		if ($btn.prop('disabled')) return;
		$btn.prop('disabled', true).html('<span class="si-spin">\u{1F504}</span>');

		frappe.call({
			method: 'sistema_industrial.api.tango_sync.sync_customers_now',
			callback: function (r) {
				const m = r.message || {};
				if (m.ok === false) {
					frappe.show_alert({
						message: __('Error al actualizar clientes: {0}', [m.error || __('desconocido')]),
						indicator: 'red',
					});
					return;
				}
				const created = m.created || 0;
				const updated = m.updated || 0;
				frappe.show_alert({
					message:
						created || updated
							? __('Clientes actualizados — {0} nuevos, {1} actualizados', [created, updated])
							: __('Clientes al día — nada nuevo desde Tango'),
					indicator: 'green',
				});
				sistema_industrial.reset_customer_link_cache(control);
			},
			error: function () {
				frappe.show_alert({
					message: __('No se pudo actualizar clientes. Reintentá en un momento.'),
					indicator: 'red',
				});
			},
			always: function () {
				$btn.prop('disabled', false).html('\u{1F504}');
			},
		});
	});

	return $btn;
};

// Limpia la caché local del control Link para que la próxima búsqueda vaya
// sí o sí al servidor. Frappe cachea resultados de search_link por
// input+término mientras el control esté montado (control.$input.cache,
// ver frappe/public/js/frappe/form/controls/link.js → on_input()) — sin
// esto, un cliente recién sincronizado podría no aparecer en el buscador
// hasta recargar la página entera.
sistema_industrial.reset_customer_link_cache = function (control) {
	if (control && control.$input) {
		control.$input.cache = {};
	}
};
