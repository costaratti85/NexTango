// Página OCR Facturas Proveedor.
//
// ESQUELETO FUNCIONAL (Atlas) — cablea los endpoints del backend de punta a
// punta para que el flujo se pueda probar. LA UI FINAL ES DE VEGA: esto es el
// mínimo para subir una factura, hacer polling y mostrar el JSON crudo del
// resultado. Vega reemplaza el render por la grilla real (líneas, matches,
// candidatos, confirmación).
//
// Endpoints (sistema_industrial.api.ocr_proveedores):
//   subir_factura(file_url) -> {job_id, status}
//   estado(job_id)          -> {status}
//   resultado(job_id)       -> {proveedor, lineas, meta}
//   confirmar_recepcion_borrador(supplier, lineas_json) -> {purchase_receipt} [STRETCH]

frappe.pages['ocr-proveedores'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'OCR Facturas Proveedor',
		single_column: true,
	});

	const $body = $(wrapper).find('.layout-main-section');
	$body.html(`
		<div class="ocr-prov">
			<p class="text-muted">Subí una factura (PDF o imagen) para extraer proveedor y líneas.</p>
			<button class="btn btn-primary btn-subir">Subir factura</button>
			<div class="ocr-estado mt-3 text-muted"></div>
			<pre class="ocr-resultado mt-3" style="white-space:pre-wrap"></pre>
		</div>
	`);

	const $estado = $body.find('.ocr-estado');
	const $res = $body.find('.ocr-resultado');

	$body.find('.btn-subir').on('click', () => {
		new frappe.ui.FileUploader({
			allow_multiple: false,
			restrictions: { allowed_file_types: ['.pdf', '.png', '.jpg', '.jpeg', '.tiff'] },
			on_success: (file_doc) => subir(file_doc.file_url),
		});
	});

	function subir(file_url) {
		$estado.text('Encolando…');
		$res.text('');
		frappe.call({
			method: 'sistema_industrial.api.ocr_proveedores.subir_factura',
			args: { file_url },
			callback: (r) => {
				if (r.message && r.message.job_id) poll(r.message.job_id);
			},
		});
	}

	function poll(job_id) {
		$estado.text('Procesando…');
		const iv = setInterval(() => {
			frappe.call({
				method: 'sistema_industrial.api.ocr_proveedores.estado',
				args: { job_id },
				callback: (r) => {
					const st = (r.message || {}).status;
					$estado.text('Estado: ' + st);
					if (['done', 'error', 'ocr_pendiente', 'unknown'].includes(st)) {
						clearInterval(iv);
						if (st === 'done') mostrar(job_id);
					}
				},
			});
		}, 1500);
	}

	function mostrar(job_id) {
		frappe.call({
			method: 'sistema_industrial.api.ocr_proveedores.resultado',
			args: { job_id },
			// Vega: reemplazar este dump por la grilla real de revisión/confirmación.
			callback: (r) => $res.text(JSON.stringify(r.message, null, 2)),
		});
	}
};
