// Indicador chico y discreto de versión (VEGA_MOSTRAR_VERSION_EN_PAGINAS,
// MSG_035 de Nova) — footer fijo en la esquina, igual en las 6 páginas.
// Lee window.SI_VERSION, que genera sistema_industrial.deploy.generate_version_stamp
// en public/js/version_stamp.js (cargado ANTES que este script — ver hooks.py).
//
// Auto-adjuntado al <body>, sin requerir ninguna integración por página: a
// diferencia de customer_sync.js (que se agrega junto a un control puntual
// de cada page), el footer es idéntico y fijo en todas partes, así que este
// archivo solo se necesita en app_include_js, nada más.
(function () {
	function pad(n) {
		return String(n).padStart(2, '0');
	}

	function format_version(v) {
		if (!v || !v.commit) return '';
		let dateStr = '';
		const d = v.deployed_at ? new Date(v.deployed_at) : null;
		if (d && !isNaN(d.getTime())) {
			dateStr = ' · ' + pad(d.getDate()) + '/' + pad(d.getMonth() + 1) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
		}
		return 'v ' + v.commit + dateStr;
	}

	function attach() {
		if (!window.SI_VERSION || document.getElementById('si-version-footer')) return;
		const el = document.createElement('div');
		el.id = 'si-version-footer';
		el.textContent = format_version(window.SI_VERSION);
		el.title = window.SI_VERSION.deployed_at ? ('Deploy: ' + window.SI_VERSION.deployed_at + ' (UTC)') : '';
		Object.assign(el.style, {
			position: 'fixed',
			bottom: '4px',
			right: '8px',
			zIndex: '1000',
			fontSize: '10px',
			fontFamily: 'monospace',
			color: '#9aa5b1',
			background: 'rgba(255,255,255,.75)',
			padding: '1px 6px',
			borderRadius: '4px',
			pointerEvents: 'none',
			userSelect: 'none',
		});
		document.body.appendChild(el);
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', attach);
	} else {
		attach();
	}
})();
