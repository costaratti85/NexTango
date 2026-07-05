// Botón "Actualizar" (sync manual Tango → ERPNext) junto a los selectores de
// Customer — compartido entre panel-decorativo, plegados-complejos,
// perfiles-plegados y corte-barras (MSG_023 de Nova). Un solo bloque en vez
// de repetir la lógica en cada page.
//
// Endpoints reales (Forge, commit 250b107, MSG_027 a Vega — reemplaza el
// intento anterior basado en Background Job, no disponible en esta
// instalación Frappe v16; ahora el estado se trackea en Redis):
//   POST sistema_industrial.tango_sync.api.manual_sync_customers
//     → { job_id, message, status: "queued" }
//   GET  sistema_industrial.tango_sync.api.get_sync_status(job_id)
//     → { status: "running"|"completed"|"failed"|"not_found"|"error",
//         created, updated, failed, total, error?, started_at?, completed_at? }
//
// VEGA_CONECTAR_POLLING_SYNC: verificado end-to-end contra el servidor real
// antes de escribir esto (no solo confiar en el reporte) — job_id generado
// upfront (no depende del valor de retorno de frappe.enqueue, que con
// enqueue_after_commit=True siempre da None — el bug que bloqueaba el
// intento anterior), status "running" confirmado, get_sync_status no
// requiere permisos especiales (Redis plano, no el doctype "RQ Job" que
// sí los requería).
frappe.provide('sistema_industrial');

const SI_SYNC_POLL_MS = 2500; // "cada 2-3s" pedido en MSG_023

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

	let pollTimer = null;

	const stopPolling = () => {
		if (pollTimer) {
			clearInterval(pollTimer);
			pollTimer = null;
		}
	};

	// Vuelve el botón a su estado normal, pase lo que pase (éxito, error, timeout).
	const finish = () => {
		stopPolling();
		$btn.prop('disabled', false)
			.html('\u{1F504}')
			.attr('title', __('Actualizar clientes desde Tango'));
	};

	const poll = (job_id) => {
		frappe.call({
			method: 'sistema_industrial.tango_sync.api.get_sync_status',
			args: { job_id },
			callback: function (r) {
				const s = r.message || {};
				if (s.status === 'completed') {
					const created = s.created || 0;
					const updated = s.updated || 0;
					const failed = s.failed || 0;
					frappe.show_alert({
						message:
							created || updated
								? __('Clientes actualizados — {0} nuevos, {1} actualizados{2}', [
										created,
										updated,
										failed ? __(' ({0} fallidos)', [failed]) : '',
								  ])
								: __('Clientes al día — nada nuevo desde Tango'),
						indicator: failed ? 'orange' : 'green',
					});
					sistema_industrial.reset_customer_link_cache(control);
					finish();
				} else if (s.status === 'failed') {
					frappe.show_alert({
						message: __('Error al sincronizar clientes: {0}', [s.error || __('desconocido')]),
						indicator: 'red',
					});
					finish();
				} else if (s.status === 'not_found' || s.status === 'error') {
					// Redis expiró (TTL 10 min) o el dato quedó corrupto — no seguir
					// esperando algo que ya no va a llegar.
					frappe.show_alert({
						message: __('No se pudo confirmar el resultado de la sincronización.'),
						indicator: 'orange',
					});
					finish();
				}
				// 'running' -> seguir esperando, el intervalo llama de nuevo solo.
			},
			error: function () {
				// Un error de red puntual en un poll no debería cortar todo el
				// ciclo — el próximo intervalo reintenta. Si Redis expira,
				// not_found lo corta igual más arriba.
			},
		});
	};

	$btn.on('click', function () {
		if ($btn.prop('disabled')) return;
		$btn.prop('disabled', true)
			.html('<span class="si-spin">\u{1F504}</span>')
			.attr('title', __('Sincronizando...'));

		frappe.call({
			method: 'sistema_industrial.tango_sync.api.manual_sync_customers',
			callback: function (r) {
				const job_id = r.message && r.message.job_id;
				if (!job_id) {
					frappe.show_alert({
						message: __('No se pudo iniciar la sincronización.'),
						indicator: 'red',
					});
					finish();
					return;
				}
				pollTimer = setInterval(() => poll(job_id), SI_SYNC_POLL_MS);
			},
			error: function () {
				frappe.show_alert({
					message: __('No se pudo iniciar la sincronización. Reintentá en un momento.'),
					indicator: 'red',
				});
				finish();
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
