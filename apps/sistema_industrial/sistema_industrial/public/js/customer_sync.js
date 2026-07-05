// Botón "Actualizar" (sync manual Tango → ERPNext) junto a los selectores de
// Customer — compartido entre panel-decorativo, plegados-complejos,
// perfiles-plegados y corte-barras (MSG_023 de Nova). Un solo bloque en vez
// de repetir la lógica en cada page.
//
// Endpoint real (Forge, commit b92f0a3, MSG_025 de Nova):
//   POST sistema_industrial.tango_sync.api.manual_sync_customers
//   respuesta inmediata: { job_id, message, status: "queued" }
//   el sync real corre en background (frappe.enqueue) — el resultado
//   ({created, updated, failed, errors}) queda en el output del job.
//
// VEGA_CONECTAR_POLLING_SYNC — BLOQUEADO, escalado a Forge (MSG_026 en su
// canal) antes de implementar el polling que pedía la tarea:
//   1. job_id siempre viene "queued_but_no_id" — frappe.enqueue(...,
//      enqueue_after_commit=True) devuelve None al llamador SIEMPRE
//      (confirmado en el servidor), así que manual_sync_customers() nunca
//      tiene un id real que devolver. El job en sí sí tiene un UUID legítimo
//      internamente, pero nunca llega al frontend.
//   2. Aunque hubiera un job_id real, el doctype "RQ Job" (la vía que
//      sugirió Forge) solo da permiso de lectura a System Manager —
//      un usuario real (SI Vendedor/Admin Produccion/Gerencia) no podría
//      consultarlo directo. Hace falta un endpoint whitelisted propio.
// Mientras tanto: dispara el sync (funciona) pero es honesto sobre no poder
// confirmar cuándo termina ni traer el resultado — sin fingir un polling
// que no puede funcionar todavía.
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
			method: 'sistema_industrial.tango_sync.api.manual_sync_customers',
			callback: function (r) {
				const m = r.message || {};
				frappe.show_alert({
					message: __(
						'Sincronización de clientes iniciada — puede tardar varios minutos. ' +
							'Todavía no hay forma de avisar cuándo termina (pendiente de backend).'
					),
					indicator: 'blue',
				});
				// Reset igual: si un sync anterior (nocturno u otro manual) ya
				// trajo algo nuevo, que se vea sin esperar a este.
				sistema_industrial.reset_customer_link_cache(control);
			},
			error: function () {
				frappe.show_alert({
					message: __('No se pudo iniciar la sincronización. Reintentá en un momento.'),
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
