// Control Link a Customer (montado en on_page_load, leído al guardar el pedido).
var _ppCustomerControl = null;

frappe.pages['perfiles-plegados'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Perfiles Plegados',
		single_column: true,
	});
	$(wrapper).find('.page-content').html(frappe.render_template('perfiles_plegados'));
	_ppCustomerControl = frappe.ui.form.make_control({
		df: {
			fieldtype: 'Link',
			options: 'Customer',
			fieldname: 'cliente',
			placeholder: __('Nombre o código de cliente'),
		},
		parent: $(wrapper).find('#pp-customer-field'),
		render_input: true,
	});
	sistema_industrial.attach_customer_sync_button(_ppCustomerControl, $(wrapper).find('#pp-customer-field'));
	perfiles_plegados_init();
};

// App portada de research/cybelec/plegado_app/index.html (main). El motor de cálculo
// (DIN 6935, secuenciador, DXF) es idéntico al standalone del iPad — cambios solo en
// ids (prefijo pp-), scoping de queries y la integración de datos (frappe.call).
function perfiles_plegados_init() {
	"use strict";
	var DEG=Math.PI/180;
	function rad(d){ return d*DEG; }
	function rot(p,thDeg){ var c=Math.cos(thDeg*DEG),s=Math.sin(thDeg*DEG); return {x:p.x*c-p.y*s,y:p.x*s+p.y*c}; }

	/* ===== MOTOR DE CÁLCULO ===== */
	function din6935_k(ri,s){ if(s<=0)return 1; var r=ri/s; if(r>=5)return 1; var k=0.65+0.5*(Math.log(r)/Math.LN10); if(k<0)k=0; if(k>1)k=1; return k; }
	function din6935_v(beta,ri,s){ if(beta<=0||beta>=165)return 0; var k=din6935_k(ri,s); return (Math.PI*beta/180)*(ri+k*s/2)-2*(ri+s)*Math.tan(rad(beta/2)); }
	function penetracion(alpha,V){ return (V/2)*Math.tan(rad((180-alpha)/2)); }
	function sensibilidad(alpha,V){ var c=Math.cos(rad((180-alpha)/2)); return Math.abs((V/2)*0.5*(1/(c*c))*Math.PI/180); }
	function tonelaje(L,s,Rm,V,coef){ coef=coef||1.33; var kN=coef*Rm*(L/1000)*(s*s)/V; return {kN:kN,ton:kN/9.81}; }

	/* ===== GEOMETRÍA REAL DE LOS ÚTILES (del DXF) ===== */
	var DIE=[[-75,-180.2],[-75,-168],[-88,-168],[-88,-148],[-75,-148],[-75,-103],[-12,-103],[-12,0],[-10,0],[0,-10],[10,0],[12,0],[12,-103],[75,-103],[75,-148],[88,-148],[88,-168],[75,-168],[75,-180.2]];
	var PUNCH_SEGS=[[[-0.0,0.0],[-6.6,6.74]],[[-6.6,6.74],[-6.86,8.61]],[[-6.86,8.61],[-19.84,21.84]],[[-19.84,21.84],[-19.84,71.73]],[[-19.84,71.73],[-16.73,71.73]],[[-16.73,71.73],[-16.73,80.07]],[[-16.73,80.07],[-19.84,80.07]],[[-19.84,80.07],[-19.84,97.31]],[[-19.84,97.31],[-7.2,97.31]],[[-7.2,97.31],[-7.2,195.24]],[[-7.2,195.24],[21.8,195.24]],[[21.8,195.24],[21.8,116.24]],[[21.8,116.24],[6.8,116.24]],[[6.8,116.24],[6.8,67.24]],[[6.8,67.24],[5.8,67.24]],[[5.8,67.24],[5.8,42.87]],[[5.8,42.87],[5.81,6.52]],[[5.81,6.52],[-0.0,0.0]]];
	var TOOLS={"punzones": [{"id": 0, "name": "Agudo 40\u00b0", "minA": 40, "ri": 0.8, "hem": false, "segs": [[[7.14, 19.98], [0.0, 0.0]], [[0.0, 0.0], [-20.0, 55.96]], [[-20.0, 55.96], [-20.0, 79.92]], [[-20.0, 79.92], [-16.5, 79.92]], [[-16.5, 79.92], [-16.5, 88.42]], [[-16.5, 88.42], [-20.0, 88.42]], [[-20.0, 88.42], [-20.0, 106.42]], [[-20.0, 106.42], [-7.0, 106.42]], [[-7.0, 106.42], [-7.0, 76.42]], [[-7.0, 76.42], [7.0, 76.42]], [[7.0, 76.42], [7.0, 61.42]], [[7.0, 61.42], [4.53, 57.71]], [[4.53, 57.71], [2.56, 53.71]], [[2.56, 53.71], [1.14, 49.49]], [[1.14, 49.49], [0.28, 45.12]], [[0.28, 45.12], [0.0, 40.67]], [[0.0, 40.67], [0.31, 36.23]], [[0.31, 36.23], [1.2, 31.86]], [[1.2, 31.86], [2.65, 27.65]], [[2.65, 27.65], [4.64, 23.66]], [[4.64, 23.66], [7.14, 19.98]]]}, {"id": 1, "name": "Aplaste (dobladillo)", "minA": 75, "ri": 0.6, "hem": true, "segs": [[[-2.11, 71.93], [-2.11, 20.3]], [[0.0, 17.69], [0.0, 0.0]], [[-19.78, 16.93], [-19.78, 0.0]], [[-16.48, 54.86], [-16.48, 20.38]], [[-2.11, 71.93], [-15.87, 71.93]], [[-15.87, 107.16], [-15.87, 71.93]], [[0.0, 0.0], [-19.78, 0.0]], [[0.0, 17.69], [-2.11, 20.3]], [[-19.78, 16.93], [-16.48, 20.38]], [[-28.05, 69.18], [-28.05, 75.44]], [[-28.05, 69.18], [-28.04, 68.87]], [[-28.04, 68.87], [-28.01, 68.55]], [[-28.01, 68.55], [-27.96, 68.24]], [[-27.96, 68.24], [-27.89, 67.94]], [[-27.89, 67.94], [-27.8, 67.64]], [[-27.8, 67.64], [-27.7, 67.34]], [[-27.7, 67.34], [-27.57, 67.05]], [[-27.57, 67.05], [-27.43, 66.77]], [[-27.43, 66.77], [-27.27, 66.5]], [[-27.27, 66.5], [-27.09, 66.24]], [[-27.09, 66.24], [-26.9, 66.0]], [[-26.9, 66.0], [-26.69, 65.76]], [[-28.05, 83.93], [-28.05, 107.16]], [[-16.48, 54.86], [-26.69, 65.76]], [[-28.05, 107.16], [-15.87, 107.16]], [[-28.05, 75.43], [-24.55, 75.43]], [[-24.55, 75.43], [-24.55, 83.93]], [[-24.55, 83.93], [-28.05, 83.93]]]}, {"id": 2, "name": "Recto", "minA": 88, "ri": 2.4, "hem": false, "segs": [[[-19.84, 21.83], [-6.86, 8.6]], [[-6.86, 8.6], [-6.6, 6.73]], [[-6.6, 6.73], [0.0, 0.0]], [[0.0, 0.0], [5.81, 6.52]], [[5.81, 6.52], [3.0, 9.49]], [[3.0, 9.49], [0.72, 12.9]], [[0.72, 12.9], [-0.96, 16.64]], [[-0.96, 16.64], [-1.99, 20.61]], [[-1.99, 20.61], [-2.33, 24.69]], [[-2.33, 24.69], [-1.99, 28.77]], [[-1.99, 28.77], [-0.97, 32.74]], [[-0.97, 32.74], [0.71, 36.48]], [[0.71, 36.48], [2.98, 39.89]], [[2.98, 39.89], [5.8, 42.87]], [[5.8, 42.87], [5.8, 67.24]], [[5.8, 67.24], [-7.2, 67.24]], [[-7.2, 67.24], [-7.2, 97.31]], [[-7.2, 97.31], [-19.84, 97.31]], [[-19.84, 97.31], [-19.84, 80.06]], [[-19.84, 80.06], [-16.73, 80.06]], [[-16.73, 80.06], [-16.73, 71.73]], [[-16.73, 71.73], [-19.84, 71.73]], [[-19.84, 71.73], [-19.84, 21.83]], [[-19.84, 21.83], [-19.84, 21.83]]]}, {"id": 3, "name": "Cuello cisne B", "minA": 88, "ri": 2.4, "hem": false, "segs": [[[-8.89, 65.0], [-7.71, 66.31]], [[-7.71, 66.31], [-6.51, 67.61]], [[-6.51, 67.61], [-5.29, 68.88]], [[-5.29, 68.88], [-4.06, 70.14]], [[-4.06, 70.14], [-2.8, 71.38]], [[-2.8, 71.38], [-1.53, 72.6]], [[-1.53, 72.6], [-0.24, 73.81]], [[-0.24, 73.81], [1.06, 74.99]], [[1.06, 74.99], [2.38, 76.16]], [[2.38, 76.16], [3.72, 77.31]], [[3.72, 77.31], [4.08, 77.64]], [[4.08, 77.64], [4.41, 78.0]], [[4.41, 78.0], [4.71, 78.39]], [[4.71, 78.39], [4.97, 78.81]], [[4.97, 78.81], [5.2, 79.24]], [[5.2, 79.24], [5.39, 79.7]], [[5.39, 79.7], [5.53, 80.17]], [[5.53, 80.17], [5.64, 80.64]], [[5.64, 80.64], [5.7, 81.13]], [[5.7, 81.13], [5.72, 81.62]], [[5.72, 81.62], [5.72, 84.09]], [[5.72, 84.09], [-7.45, 84.09]], [[-7.45, 84.09], [-7.45, 113.98]], [[-7.45, 113.98], [-19.73, 113.98]], [[-19.73, 113.98], [-19.73, 96.72]], [[-19.73, 96.72], [-16.24, 96.72]], [[-16.24, 96.72], [-16.24, 88.33]], [[-16.24, 88.33], [-19.9, 88.33]], [[-19.9, 88.33], [-19.9, 84.02]], [[-19.9, 84.02], [-33.64, 84.02]], [[-33.64, 84.02], [-33.64, 35.07]], [[-33.64, 35.07], [-6.63, 7.63]], [[-6.63, 7.63], [-6.63, 6.74]], [[-6.63, 6.74], [-0.0, 0.0]], [[-0.0, 0.0], [5.05, 4.97]], [[5.05, 4.97], [-11.32, 21.59]], [[-11.32, 21.59], [-11.38, 25.34]], [[-11.38, 25.34], [-11.42, 29.08]], [[-11.42, 29.08], [-11.45, 32.83]], [[-11.45, 32.83], [-11.47, 36.57]], [[-11.47, 36.57], [-11.47, 40.32]], [[-11.47, 40.32], [-11.45, 44.06]], [[-11.45, 44.06], [-11.42, 47.81]], [[-11.42, 47.81], [-11.37, 51.55]], [[-11.37, 51.55], [-11.31, 55.29]], [[-11.31, 55.29], [-11.24, 59.04]], [[-11.24, 59.04], [-11.2, 59.69]], [[-11.2, 59.69], [-11.11, 60.34]], [[-11.11, 60.34], [-10.99, 60.98]], [[-10.99, 60.98], [-10.81, 61.61]], [[-10.81, 61.61], [-10.59, 62.23]], [[-10.59, 62.23], [-10.33, 62.83]], [[-10.33, 62.83], [-10.03, 63.41]], [[-10.03, 63.41], [-9.69, 63.97]], [[-9.69, 63.97], [-9.31, 64.5]], [[-9.31, 64.5], [-8.89, 65.0]]]}, {"id": 4, "name": "Largo", "minA": 88, "ri": 2.4, "hem": false, "segs": [[[6.75, 102.86], [6.75, 119.37]], [[6.75, 119.37], [-6.79, 119.37]], [[-6.79, 119.37], [-6.79, 149.39]], [[-6.79, 149.39], [-19.77, 149.39]], [[-19.77, 149.39], [-19.77, 132.9]], [[-19.77, 132.9], [-16.95, 132.9]], [[-16.95, 132.9], [-16.95, 123.84]], [[-16.95, 123.84], [-19.77, 123.84]], [[-19.77, 123.84], [-19.77, 19.77]], [[-19.77, 19.77], [0.0, 0.0]], [[0.0, 0.0], [7.0, 7.0]], [[7.0, 7.0], [7.0, 11.27]], [[7.0, 11.27], [-0.01, 18.28]], [[-0.01, 18.28], [-0.01, 96.1]], [[-0.01, 96.1], [6.75, 102.86]]]}], "matrices": [{"id": 0, "name": "Aguda V24 40\u00b0", "multi": false, "rotations": [{"V": 24, "angle": 40, "depth": 22, "minA": 40, "segs": [[[15.23, -0.06], [11.81, -0.11]], [[11.81, -0.11], [11.49, -0.13]], [[11.49, -0.13], [11.18, -0.19]], [[11.18, -0.19], [10.88, -0.29]], [[10.88, -0.29], [10.59, -0.42]], [[10.59, -0.42], [10.32, -0.59]], [[10.32, -0.59], [10.07, -0.78]], [[10.07, -0.78], [9.85, -1.01]], [[9.85, -1.01], [9.65, -1.26]], [[9.65, -1.26], [9.49, -1.53]], [[9.49, -1.53], [9.36, -1.82]], [[9.36, -1.82], [1.66, -22.06]], [[1.66, -22.06], [1.46, -22.44]], [[1.46, -22.44], [1.18, -22.76]], [[1.18, -22.76], [0.83, -23.0]], [[0.83, -23.0], [0.43, -23.15]], [[0.43, -23.15], [0.0, -23.2]], [[0.0, -23.2], [-0.42, -23.15]], [[-0.42, -23.15], [-0.82, -22.99]], [[-0.82, -22.99], [-1.17, -22.74]], [[-1.17, -22.74], [-1.45, -22.42]], [[-1.45, -22.42], [-1.65, -22.04]], [[-1.65, -22.04], [-8.98, -2.0]], [[-8.98, -2.0], [-9.13, -1.67]], [[-9.13, -1.67], [-9.31, -1.36]], [[-9.31, -1.36], [-9.53, -1.07]], [[-9.53, -1.07], [-9.78, -0.81]], [[-9.78, -0.81], [-10.07, -0.59]], [[-10.07, -0.59], [-10.38, -0.4]], [[-10.38, -0.4], [-10.71, -0.25]], [[-10.71, -0.25], [-11.05, -0.14]], [[-11.05, -0.14], [-11.41, -0.07]], [[-11.41, -0.07], [-11.77, -0.05]], [[-11.77, -0.05], [-15.01, -0.05]], [[-15.01, -0.05], [-15.01, -42.71]], [[-15.01, -42.71], [-5.7, -42.71]], [[-5.7, -42.71], [-5.7, -58.04]], [[-5.7, -58.04], [5.91, -58.04]], [[5.91, -58.04], [5.91, -42.71]], [[5.91, -42.71], [15.23, -42.71]], [[15.23, -42.71], [15.22, -0.06]]]}]}, {"id": 1, "name": "V20 90\u00b0", "multi": false, "rotations": [{"V": 20, "angle": 90, "depth": 10, "minA": 88, "segs": [[[-75.03, -180.2], [-75.03, -168.0]], [[-75.03, -168.0], [-88.03, -168.0]], [[-88.03, -168.0], [-88.03, -148.0]], [[-88.03, -148.0], [-75.03, -148.0]], [[-75.03, -148.0], [-75.03, -103.0]], [[-75.03, -103.0], [-12.03, -103.0]], [[-12.03, -103.0], [-12.03, 0.0]], [[-12.03, 0.0], [-10.03, 0.0]], [[-10.03, 0.0], [-0.03, -10.0]], [[-0.03, -10.0], [9.97, 0.0]], [[9.97, 0.0], [11.97, 0.0]], [[11.97, 0.0], [11.97, -103.0]], [[11.97, -103.0], [74.97, -103.0]], [[74.97, -103.0], [74.97, -148.0]], [[74.97, -148.0], [87.97, -148.0]], [[87.97, -148.0], [87.97, -168.0]], [[87.97, -168.0], [74.97, -168.0]], [[74.97, -168.0], [74.97, -180.2]], [[-75.03, -180.2], [74.97, -180.2]]]}]}, {"id": 2, "name": "Cuadrada (4 V)", "multi": true, "rotations": [{"V": 6, "angle": 88, "depth": 3.3, "minA": 88, "segs": [[[-12.66, 0.0], [-8.09, -4.57]], [[-8.09, -4.57], [-3.51, 0.0]], [[-3.51, 0.0], [2.69, 0.0]], [[2.69, 0.0], [14.16, -11.48]], [[14.16, -11.48], [25.64, 0.0]], [[25.64, 0.0], [37.8, 0.0]], [[37.8, 0.0], [40.43, -2.63]], [[40.43, -2.63], [43.06, 0.0]], [[43.06, 0.0], [45.16, 0.0]], [[45.16, 0.0], [45.16, -11.45]], [[45.16, -11.45], [25.62, -31.0]], [[25.62, -31.0], [45.16, -50.55]], [[45.16, -50.55], [45.16, -62.0]], [[45.16, -62.0], [42.34, -62.0]], [[42.34, -62.0], [36.47, -56.13]], [[36.47, -56.13], [30.59, -62.0]], [[30.59, -62.0], [23.21, -62.0]], [[23.21, -62.0], [14.16, -52.96]], [[14.16, -52.96], [5.12, -62.0]], [[5.12, -62.0], [-0.05, -62.0]], [[-0.05, -62.0], [-5.46, -56.59]], [[-5.46, -56.59], [-10.86, -62.0]], [[-10.86, -62.0], [-16.84, -62.0]], [[-16.84, -62.0], [-16.84, -48.52]], [[-16.84, -48.52], [0.0, -31.68]], [[0.0, -31.68], [-16.84, -14.84]], [[-16.84, -14.84], [-16.84, 0.0]], [[-16.84, 0.0], [-12.66, 0.0]]]}, {"V": 12, "angle": 88, "depth": 6.6, "minA": 88, "segs": [[[-52.96, -57.82], [-48.38, -53.25]], [[-48.38, -53.25], [-52.96, -48.67]], [[-52.96, -48.67], [-52.96, -42.48]], [[-52.96, -42.48], [-41.48, -31.0]], [[-41.48, -31.0], [-52.96, -19.52]], [[-52.96, -19.52], [-52.96, -7.37]], [[-52.96, -7.37], [-50.32, -4.73]], [[-50.32, -4.73], [-52.96, -2.1]], [[-52.96, -2.1], [-52.96, 0.0]], [[-52.96, 0.0], [-41.5, 0.0]], [[-41.5, 0.0], [-21.96, -19.55]], [[-21.96, -19.55], [-2.41, 0.0]], [[-2.41, 0.0], [9.04, 0.0]], [[9.04, 0.0], [9.04, -2.83]], [[9.04, -2.83], [3.17, -8.7]], [[3.17, -8.7], [9.04, -14.57]], [[9.04, -14.57], [9.04, -21.96]], [[9.04, -21.96], [0.0, -31.0]], [[0.0, -31.0], [9.04, -40.04]], [[9.04, -40.04], [9.04, -45.22]], [[9.04, -45.22], [3.64, -50.62]], [[3.64, -50.62], [9.04, -56.02]], [[9.04, -56.02], [9.04, -62.0]], [[9.04, -62.0], [-4.43, -62.0]], [[-4.43, -62.0], [-21.27, -45.16]], [[-21.27, -45.16], [-38.11, -62.0]], [[-38.11, -62.0], [-52.96, -62.0]], [[-52.96, -62.0], [-52.96, -57.82]]]}, {"V": 8, "angle": 88, "depth": 4.4, "minA": 88, "segs": [[[38.28, -62.0], [33.71, -57.42]], [[33.71, -57.42], [29.13, -62.0]], [[29.13, -62.0], [22.93, -62.0]], [[22.93, -62.0], [11.45, -50.52]], [[11.45, -50.52], [-0.02, -62.0]], [[-0.02, -62.0], [-12.18, -62.0]], [[-12.18, -62.0], [-14.81, -59.37]], [[-14.81, -59.37], [-17.44, -62.0]], [[-17.44, -62.0], [-19.55, -62.0]], [[-19.55, -62.0], [-19.55, -50.55]], [[-19.55, -50.55], [0.0, -31.0]], [[0.0, -31.0], [-19.55, -11.45]], [[-19.55, -11.45], [-19.55, 0.0]], [[-19.55, 0.0], [-16.72, 0.0]], [[-16.72, 0.0], [-10.85, -5.87]], [[-10.85, -5.87], [-4.97, 0.0]], [[-4.97, 0.0], [2.41, 0.0]], [[2.41, 0.0], [11.45, -9.04]], [[11.45, -9.04], [20.5, 0.0]], [[20.5, 0.0], [25.67, 0.0]], [[25.67, 0.0], [31.07, -5.4]], [[31.07, -5.4], [36.48, 0.0]], [[36.48, 0.0], [42.45, 0.0]], [[42.45, 0.0], [42.45, -13.48]], [[42.45, -13.48], [25.62, -30.32]], [[25.62, -30.32], [42.45, -47.16]], [[42.45, -47.16], [42.45, -62.0]], [[42.45, -62.0], [38.28, -62.0]]]}, {"V": 16, "angle": 88, "depth": 8.8, "minA": 88, "segs": [[[11.47, -4.17], [6.9, -8.75]], [[6.9, -8.75], [11.47, -13.32]], [[11.47, -13.32], [11.47, -19.52]], [[11.47, -19.52], [-0.0, -31.0]], [[-0.0, -31.0], [11.47, -42.48]], [[11.47, -42.48], [11.47, -54.63]], [[11.47, -54.63], [8.84, -57.26]], [[8.84, -57.26], [11.47, -59.89]], [[11.47, -59.89], [11.47, -62.0]], [[11.47, -62.0], [0.02, -62.0]], [[0.02, -62.0], [-19.53, -42.45]], [[-19.53, -42.45], [-39.07, -62.0]], [[-39.07, -62.0], [-50.53, -62.0]], [[-50.53, -62.0], [-50.53, -59.17]], [[-50.53, -59.17], [-44.65, -53.3]], [[-44.65, -53.3], [-50.53, -47.43]], [[-50.53, -47.43], [-50.53, -40.04]], [[-50.53, -40.04], [-41.48, -31.0]], [[-41.48, -31.0], [-50.53, -21.96]], [[-50.53, -21.96], [-50.53, -16.78]], [[-50.53, -16.78], [-45.12, -11.38]], [[-45.12, -11.38], [-50.53, -5.97]], [[-50.53, -5.97], [-50.53, 0.0]], [[-50.53, 0.0], [-37.05, 0.0]], [[-37.05, 0.0], [-20.21, -16.84]], [[-20.21, -16.84], [-3.37, 0.0]], [[-3.37, 0.0], [11.47, 0.0]], [[11.47, 0.0], [11.47, -4.17]]]}]}]};
	var curPunch=null, curDie=null;
	var TABLE_HALF=88, X_MIN=5, X_MAX=600, DIE_DEPTH=10, FINGER_H=30;   // FINGER_H: altura útil del dedo del tope (mm)
	var MACHINE_CLIP=160;   // zoom de la vista de máquina: mm visibles a cada lado del vértice de pliegue
	var curRot=0;
	function dieRot(){ return (curDie&&curDie.rotations)?curDie.rotations[curRot]:null; }
	function penClamp(alpha,V){ var r=dieRot(); var d=(r&&r.depth)?r.depth:DIE_DEPTH; return Math.min(penetracion(alpha,V), d); }
	function punchSegs(){ return (curPunch&&curPunch.segs)?curPunch.segs:PUNCH_SEGS; }

	function segInt(a,b,c,d){
	  function cr(o,p,q){ return (p.x-o.x)*(q.y-o.y)-(p.y-o.y)*(q.x-o.x); }
	  var d1=cr(c,d,a),d2=cr(c,d,b),d3=cr(a,b,c),d4=cr(a,b,d);
	  return ((d1>0&&d2<0)||(d1<0&&d2>0))&&((d3>0&&d4<0)||(d3<0&&d4>0));
	}
	// Shimrat 1962 even-odd ray casting — p inside die polygon segs?
	function pointInPoly(p, segs) {
	  var cross = 0;
	  for (var i = 0; i < segs.length; i++) {
	    var ay = segs[i][0][1], by = segs[i][1][1];
	    if ((ay > p.y) !== (by > p.y)) {
	      var ax = segs[i][0][0], bx = segs[i][1][0];
	      if (p.x < ax + (p.y - ay) * (bx - ax) / (by - ay)) cross++;
	    }
	  }
	  return (cross & 1) === 1;
	}

	/* ===== CEREBRO ===== */
	function profile(fl,an,dr,done){
	  var pts=[{x:0,y:0}], fdir=[], dir=0,x=0,y=0;
	  for(var i=0;i<fl.length;i++){ fdir.push(dir); x+=fl[i]*Math.cos(dir*DEG); y+=fl[i]*Math.sin(dir*DEG); pts.push({x:x,y:y}); if(i<an.length&&done[i]) dir+=dr[i]*(180-an[i]); }
	  return {pts:pts,fdir:fdir};
	}
	function place(fl,an,dr,done,bi,mx,my,s){
	  var pr=profile(fl,an,dr,done), pts=pr.pts, fdir=pr.fdir;
	  var th=-fdir[bi]; var bp=rot(pts[bi+1],th); var rest=s;
	  var P=pts.map(function(p){ var q=rot(p,th); q={x:q.x-bp.x,y:q.y-bp.y+rest}; if(mx)q.x=-q.x; if(my)q.y=2*rest-q.y; return q; });
	  var segs=[]; for(var i=0;i<fl.length;i++) segs.push({a:P[i],b:P[i+1],tip:(i===bi||i===bi+1),idx:i});
	  return {P:P,segs:segs,rest:rest,bi:bi};
	}
	var DIE_SEGS=(function(){ var s=[]; for(var i=0;i<DIE.length-1;i++) s.push([DIE[i],DIE[i+1]]); s.push([DIE[DIE.length-1],DIE[0]]); return s; })();
	function clearCheck(pl,alpha,V,s){   // sólo choques: con la matriz/bancada (abajo) y con el punzón
	  var pen=penClamp(alpha,V), tipY=-pen;
	  var PS=punchSegs(); var punch=[]; for(var u=0;u<PS.length;u++){ var g=PS[u]; if(Math.min(g[0][1],g[1][1])<=95) punch.push([{x:g[0][0],y:g[0][1]+tipY},{x:g[1][0],y:g[1][1]+tipY}]); }
	  var DR=dieRot(),DS=(DR&&DR.segs)?DR.segs:DIE_SEGS;
	  // 1) nodos DENTRO del perfil CAD de la matriz (incluye bancada)
	  for(var i=0;i<pl.P.length;i++){ var p=pl.P[i]; if(p.y<-1.0 && pointInPoly(p,DS)) return {clear:false,why:'una parte de la pieza queda dentro de la matriz/bancada'}; }
	  // 2) tramos de la pieza que ATRAVIESAN el perfil (alas colgando que cruzan matriz o bancada
	  //    sin dejar ningún nodo adentro — el chequeo por nodos solo no lo ve)
	  for(var k=0;k<pl.segs.length;k++){ var sg=pl.segs[k]; if(sg.tip) continue;
	    if(Math.min(sg.a.y,sg.b.y)>=-1.0) continue;                       // no baja del nivel de mesa: no puede cruzar
	    for(var q=0;q<DS.length;q++){ var dd=DS[q];
	      if(segInt(sg.a,sg.b,{x:dd[0][0],y:dd[0][1]},{x:dd[1][0],y:dd[1][1]})) return {clear:false,why:'una parte de la pieza atraviesa la matriz o la bancada'}; } }
	  // 3) choque con el punzón
	  for(var k2=0;k2<pl.segs.length;k2++){ var sg2=pl.segs[k2]; if(sg2.tip) continue; for(var q2=0;q2<punch.length;q2++){ if(segInt(sg2.a,sg2.b,punch[q2][0],punch[q2][1])) return {clear:false,why:'una parte ya plegada choca con el punzón'}; } }
	  // 4) FIN DE CARRERA: la pieza PLEGADA (brazos levantados, vértice en la V) tampoco puede
	  //    tocar el punzón ni la matriz. El dibujo lo mostraba en rojo pero el cerebro no lo
	  //    miraba: elegía secuencias que chocan al fondo del golpe (reporte de Constantino).
	  if(pl.bi!=null){
	    // Tolerancia de taller: una penetración nominal chica (radio de canto, retorno,
	    // flexión de la chapa) se tolera; un barrido profundo no.
	    var TOL_PEN=2.5;   // mm
	    var punchA=[], pxMin=1e9, pxMax=-1e9, pyMax=-1e9;
	    for(var uc=0;uc<PS.length;uc++){ var gc=PS[uc]; if(Math.min(gc[0][1],gc[1][1])<=95){
	      var sA=[[gc[0][0],gc[0][1]-pen],[gc[1][0],gc[1][1]-pen]]; punchA.push(sA);
	      pxMin=Math.min(pxMin,sA[0][0],sA[1][0]); pxMax=Math.max(pxMax,sA[0][0],sA[1][0]); pyMax=Math.max(pyMax,sA[0][1],sA[1][1]); } }
	    var bi=pl.bi, half=(180-alpha)/2;
	    var sideL=(pl.P[bi].x<=pl.P[bi+1].x)?-1:1;
	    var FP=pl.P.map(function(pt,idx){
	      var a=(idx<=bi)?sideL*half:(idx>=bi+2?-sideL*half:0);
	      var dx=pt.x, dy=pt.y-pl.rest, c=Math.cos(a*DEG), sn=Math.sin(a*DEG);
	      return {x:dx*c-dy*sn, y:(dx*sn+dy*c)+pl.rest-pen};
	    });
	    for(var kf=0;kf<pl.segs.length;kf++){ var sf=pl.segs[kf]; if(sf.tip) continue;
	      var fa=FP[sf.idx], fb=FP[sf.idx+1];
	      // poda: tramo totalmente afuera de la caja del punzón → no puede tocarlo
	      if(!(Math.max(fa.x,fb.x)<pxMin || Math.min(fa.x,fb.x)>pxMax || Math.min(fa.y,fb.y)>pyMax)){
	        var hitP=false; for(var qf=0;qf<punchA.length;qf++){ var pq=punchA[qf]; if(segInt(fa,fb,{x:pq[0][0],y:pq[0][1]},{x:pq[1][0],y:pq[1][1]})){ hitP=true; break; } }
	        if(hitP && penDepth(fa,fb,punchA)>TOL_PEN) return {clear:false,why:'al fondo del golpe una parte ya plegada barre contra el punzón'};
	      }
	      if(Math.min(fa.y,fb.y)<-1.0){
	        var hitD=false; for(var qd=0;qd<DS.length;qd++){ var d2=DS[qd]; if(segInt(fa,fb,{x:d2[0][0],y:d2[0][1]},{x:d2[1][0],y:d2[1][1]})){ hitD=true; break; } }
	        if(hitD && penDepth(fa,fb,DS)>TOL_PEN) return {clear:false,why:'al fondo del golpe la pieza barre contra la matriz'};
	      }
	    }
	  }
	  return {clear:true};
	}
	function distSeg(p,sg){ var ax=sg[0][0],ay=sg[0][1],bx=sg[1][0],by=sg[1][1]; var dx=bx-ax,dy=by-ay; var L2=dx*dx+dy*dy||1e-9; var t=((p.x-ax)*dx+(p.y-ay)*dy)/L2; t=Math.max(0,Math.min(1,t)); return Math.hypot(p.x-(ax+dx*t), p.y-(ay+dy*t)); }
	function penDepth(a,b,segs){   // penetración máxima del tramo a-b dentro del contorno (muestreo)
	  var maxd=0, N=14;
	  for(var i=0;i<=N;i++){ var t=i/N, p={x:a.x+(b.x-a.x)*t, y:a.y+(b.y-a.y)*t};
	    if(!pointInPoly(p,segs)) continue;
	    var dmin=1e9; for(var q=0;q<segs.length;q++){ var d=distSeg(p,segs[q]); if(d<dmin)dmin=d; }
	    if(dmin>maxd) maxd=dmin;
	  }
	  return maxd;
	}
	function nodeFlat(pl,gi){   // ¿el nodo gi tiene un segmento horizontal apoyado a nivel de mesa? (apoyo estable, no inclinado)
	  var lvl=pl.rest+1.5;
	  for(var k=0;k<pl.segs.length;k++){ var sg=pl.segs[k]; if(sg.idx!==gi && sg.idx!==gi-1) continue;
	    if(sg.a.y<=lvl && sg.b.y<=lvl && Math.abs(sg.a.y-sg.b.y)<1.0) return true; }
	  return false;
	}
	function feasible(pl,alpha,V,s){
	  var c=clearCheck(pl,alpha,V,s);
	  // el tope para donde topa el material más atrás que el dedo alcanza: el dedo trabaja a la
	  // altura de la mesa (banda [mesa, mesa+FINGER_H]) — un nodo COLGANDO por debajo no topea
	  var xr=-1e9, gi=-1;
	  for(var m=0;m<pl.P.length;m++){ var p=pl.P[m]; if(p.y>=-1.5 && p.y<=pl.rest+FINGER_H && p.x>xr){ xr=p.x; gi=m; } }
	  if(gi<0){ xr=pl.P[0].x; gi=0; for(var m2=1;m2<pl.P.length;m2++) if(pl.P[m2].x>xr){ xr=pl.P[m2].x; gi=m2; } }
	  var X=xr, stable=nodeFlat(pl,gi);   // ¿apoya sobre algo plano? (criterio Cybelec: no apoyar en segmento inclinado)
	  // longitud del lado del OPERARIO (lo que sobresale hacia adelante/izquierda para sostener)
	  var minx=1e9; for(var mm=0;mm<pl.P.length;mm++) if(pl.P[mm].x<minx) minx=pl.P[mm].x;
	  var op=-minx;
	  if(!c.clear) return {ok:false,why:c.why,X:X,gauge:gi,op:op,stable:stable};
	  if(X<X_MIN) return {ok:false,why:'ala muy corta para el tope ('+X.toFixed(0)+' mm)',X:X,gauge:gi,op:op,stable:stable};
	  if(X>X_MAX) return {ok:false,why:'fuera del recorrido del tope ('+X.toFixed(0)+' mm)',X:X,gauge:gi,op:op,stable:stable};
	  return {ok:true,X:X,gauge:gi,op:op,stable:stable};
	}
	/* ===== MODO MANUAL: colocar para un pliegue y un nodo de apoyo elegidos ===== */
	function placeManual(fl,an,dr,done,bi,gn,V,s){
	  var myF=(dr[bi]<0); var opts=[[false,myF],[true,myF]], best=null;   // my == signo del pliegue; girar (mx) no cambia el lado del pliegue
	  for(var o=0;o<opts.length;o++){
	    var pl=place(fl,an,dr,done,bi,opts[o][0],opts[o][1],s);
	    if(gn>=pl.P.length) continue;
	    var node=pl.P[gn], atLevel=(node.y>=-1.5 && node.y<=pl.rest+FINGER_H), cl=clearCheck(pl,an[bi],V,s);
	    var X=node.x, ok=cl.clear&&atLevel&&X>=X_MIN&&X<=X_MAX;
	    var why = !cl.clear ? cl.why : (!atLevel? 'el nodo '+nodeLetter(gn)+' no queda apoyado en el tope para este pliegue' : (X<X_MIN?'apoyo muy cerca de la línea de pliegue':(X>X_MAX?'fuera del recorrido del tope':'')));
	    var score=(ok?0:10000)+(atLevel?0:5000)+(cl.clear?0:3000)+Math.max(0,X_MIN-X)+Math.max(0,X-X_MAX)-X*0.001;
	    var cand={mx:opts[o][0],my:opts[o][1],X:X,ok:ok,why:why,pl:pl,score:score};
	    if(!best||cand.score<best.score) best=cand;
	  }
	  return best;
	}
	function simulateManual(fl,an,dr,manSeq,V,s){
	  var done=[]; for(var i=0;i<an.length;i++) done.push(false);
	  var steps=[];
	  for(var k=0;k<manSeq.length;k++){
	    var bi=manSeq[k].bend, gn=manSeq[k].node;
	    if(bi==null||gn==null){ steps.push({order:k+1,bend:bi,alpha:bi!=null?an[bi]:0,X:0,mx:false,my:false,ok:false,why:'falta elegir pliegue o apoyo',gauge:gn}); continue; }
	    var b=placeManual(fl,an,dr,done,bi,gn,V,s);
	    steps.push({order:k+1,bend:bi,alpha:an[bi],X:b?b.X:0,mx:b?b.mx:false,my:b?b.my:false,ok:b?b.ok:false,why:b?b.why:'sin colocación',gauge:gn});
	    done[bi]=true;
	  }
	  return {steps:steps};
	}
	var SIM_CACHE={};   // geometría por (pliegues hechos, pliegue actual) — no depende del orden previo
	function simulateOrder(fl,an,dr,order,V,s,preDone,maxCol){
	  if(maxCol==null) maxCol=Infinity;
	  var done=preDone?preDone.slice():[]; if(!preDone){ for(var i=0;i<an.length;i++) done.push(false); }
	  var mask=0; for(var mi=0;mi<an.length;mi++) if(done[mi]) mask|=(1<<mi);
	  var totalDev=0; for(var t=0;t<fl.length;t++) totalDev+=(fl[t]||0);
	  var minOp=Math.max(25, 0.20*totalDev);   // L. MÍN. CONTRA OPERARIO: lo que necesita para sostener
	  var steps=[], prevMx=null, prevMy=null, prevGauge=null, flips=0, giras=0, collisions=0, totalX=0, opViol=0, unstable=0, refChg=0;
	  for(var k=0;k<order.length;k++){
	    var bi=order[k], myF=(dr[bi]<0), feas, fallback;
	    var ck=mask+':'+bi, cc=SIM_CACHE[ck];
	    if(cc){ feas=cc.feas.slice(); fallback=cc.fallback; }
	    else {
	      feas=[]; fallback=null;
	      // 2 orientaciones válidas: my == signo del pliegue. La máquina siempre pliega hacia arriba:
	      // dar vuelta la pieza (my) invierte de qué lado sale el pliegue; girarla (mx, otro extremo
	      // al tope) NO lo cambia. La regla vieja (mx XOR my) permitía girada+dada vuelta para
	      // pliegues positivos y el pliegue salía del lado contrario al dibujado.
	      var opts=[[false,myF],[true,myF]];
	      for(var o=0;o<opts.length;o++){
	        var pl=place(fl,an,dr,done,bi,opts[o][0],opts[o][1],s); var f=feasible(pl,an[bi],V,s);
	        if(f.ok) feas.push({mx:opts[o][0],my:opts[o][1],X:f.X,gauge:f.gauge,op:f.op,stable:f.stable});
	        else if(!fallback) fallback={mx:opts[o][0],my:opts[o][1],X:f.X||0,gauge:f.gauge,op:f.op||0,stable:f.stable,ok:false,why:f.why};
	      }
	      SIM_CACHE[ck]={feas:feas.slice(),fallback:fallback};
	    }
	    var ch, pmx=prevMx, pg=prevGauge;
	    if(feas.length){
	      feas.sort(function(a,b){
	        var ao=(a.op>=minOp?0:1), bo=(b.op>=minOp?0:1); if(ao!==bo) return ao-bo;   // 1) que el operario lo pueda sostener
	        if(a.stable!==b.stable) return a.stable?-1:1;                                 // 2) apoyo plano/estable (no inclinado)
	        var ar=(pg!=null&&a.gauge===pg)?0:1, br=(pg!=null&&b.gauge===pg)?0:1; if(ar!==br) return ar-br; // 3) reusar mismo tope
	        var ag=(pmx===null||a.mx===pmx)?0:1, bg=(pmx===null||b.mx===pmx)?0:1; if(ag!==bg) return ag-bg;  // 4) menos girar
	        return a.X-b.X;                                                                // 5) apoyo más cercano
	      });
	      ch=feas[0]; ch.ok=true;
	    } else ch=fallback||{mx:false,my:myF,X:0,gauge:null,op:0,stable:false,ok:false,why:'sin colocación'};
	    if(!ch.ok){ collisions++;
	      // poda: ya choca más que el mejor orden conocido — este no puede ganar
	      if(collisions>maxCol) return {aborted:true,collisions:collisions};
	    }
	    if(ch.op<minOp) opViol++;
	    if(ch.ok && !ch.stable) unstable++;                                    // apoya sobre segmento inclinado (a evitar)
	    if(prevGauge!=null && ch.gauge!=null && ch.gauge!==prevGauge) refChg++; // recolocó el tope contra otro nodo
	    if(prevMy!==null && ch.my!==prevMy) flips++;
	    if(prevMx!==null && ch.mx!==prevMx) giras++;
	    prevMx=ch.mx; prevMy=ch.my; if(ch.gauge!=null) prevGauge=ch.gauge; totalX+=ch.X;
	    steps.push({order:k+1,bend:bi,alpha:an[bi],X:ch.X,mx:ch.mx,my:ch.my,ok:ch.ok,why:ch.why,gauge:ch.gauge,op:ch.op,stable:ch.stable});
	    done[bi]=true; mask|=(1<<bi);
	  }
	  return {ok:collisions===0,collisions:collisions,opViol:opViol,unstable:unstable,refChg:refChg,flips:flips,giras:giras,manips:flips+giras,steps:steps,totalX:totalX,minOp:minOp};
	}
	function permsOf(arr){
	  if(arr.length<=1) return [arr.slice()];
	  var out=[]; for(var i=0;i<arr.length;i++){ var rest=arr.slice(0,i).concat(arr.slice(i+1)); var sub=permsOf(rest); for(var j=0;j<sub.length;j++) out.push([arr[i]].concat(sub[j])); }
	  return out;
	}
	function buscarOrden(fl,an,dr,V,s,preDone){
	  SIM_CACHE={};   // dims/útiles pueden haber cambiado
	  var idx=[]; for(var i=0;i<an.length;i++){ if(!preDone||!preDone[i]) idx.push(i); }
	  var best=null, feasibleCount=0, tried=0, all=permsOf(idx);
	  for(var p=0;p<all.length && tried<=40320;p++){ tried++;
	    var r=simulateOrder(fl,an,dr,all[p],V,s,preDone,best?best.collisions:Infinity);
	    if(r.aborted) continue;   // podado: chocaba más que el mejor conocido
	    if(r.collisions===0&&r.opViol===0&&r.unstable===0) feasibleCount++;
	    // prioridad Cybelec: sin choque > operario sostiene > apoyo plano > mínimo voltear > mínimo girar > menos recolocar tope > tope cercano
	    r.score=r.collisions*1e9 + r.opViol*1e7 + r.unstable*5e6 + r.flips*1e5 + r.giras*2e3 + r.refChg*1e3 + r.totalX*0.5;
	    if(!best || r.score<best.score){ r.order=all[p]; best=r; }
	  }
	  return {best:best,feasibleCount:feasibleCount,tried:tried};
	}
	// Técnica W: genera el plan de 4 pasos cuando el perfil U/C no tiene secuencia directa
	function tryWBend(flanges,angles,dirs,V,ri,s,cal,sb){
	  if(angles.length<2) return null;
	  for(var i=1;i<dirs.length;i++) if(dirs[i]!==dirs[0]) return null; // distinto sentido = no es U/C
	  var maxF=0; for(var i=0;i<flanges.length;i++) if((flanges[i]||0)>maxF) maxF=flanges[i]||0;
	  if(maxF<60) return null; // alas muy cortas — la técnica W no aporta nada
	  var webIdx=Math.floor((flanges.length-1)/2), webLen=flanges[webIdx]||80, xg=(cal&&cal.xg)||0;
	  function Yfor(a){ var c=(state.angCorr&&state.angCorr[a])||0; var aF=a-sb-c; return cal.y90+cal.sign*(penetracion(aF,V)-penetracion(90-sb,V)); }
	  var pNom=curPunch?curPunch.name:'Recto', dNom=curDie?curDie.name:('V'+V+' 90°');
	  var flatNom='Punzón plano (Aplaste)';
	  for(var j=0;j<TOOLS.punzones.length;j++) if(TOOLS.punzones[j].hem){flatNom=TOOLS.punzones[j].name;break;}
	  var preA=20, steps=[];
	  steps.push({paso:1,tipo:'pre',
	    label:'Pliegue provisorio central',
	    hint:preA+'° en el centro del alma · tope X = '+(webLen/2).toFixed(0)+' mm (mitad del alma)',
	    X:((webLen/2)+xg).toFixed(1), Y:Yfor(preA).toFixed(2), punch:pNom, die:dNom});
	  for(var b=0;b<angles.length;b++){
	    var fl=(b===0)?(flanges[0]||50):(flanges[flanges.length-1]||50);
	    steps.push({paso:b+2,tipo:'bend',
	      label:'Pliegue b'+(b+1)+' — ala '+(b===0?'izquierda':'derecha'),
	      hint:angles[b]+'° · tope X = '+(fl+xg).toFixed(0)+' mm',
	      X:(fl+xg).toFixed(1), Y:Yfor(angles[b]).toFixed(2), punch:pNom, die:dNom});
	  }
	  steps.push({paso:angles.length+2,tipo:'aplaste',
	    label:'Aplaste del pliegue provisorio',
	    hint:'Girar la pieza (forma W). Colocar el pliegue central sobre el PUNZÓN PLANO + MATRIZ PLANA y aplastar → perfil U final.',
	    X:((webLen/2)+xg).toFixed(1), Y:'—', punch:flatNom, die:'Matriz plana'});
	  return steps;
	}
	// Técnica de escalón (joggle): dos pliegues opuestos pegados con ala corta en el medio no
	// salen directo. Se pre-pliegan LOS DOS a 135° con la chapa plana (topeando del extremo
	// final, X desarrollado) y se cierran a 90° después; el resto de los pliegues se secuencia
	// normal con los escalones ya dados por hechos.
	function tryJoggle(fl,an,dr,V,ri,s,cal,sb){
	  if(an.length<2) return null;
	  var pairs=[];
	  for(var i=0;i<an.length-1;i++){
	    if(dr[i]!==dr[i+1] && (fl[i+1]||0)<=V*1.25){ pairs.push(i); i++; }   // pares sin solapar
	  }
	  if(!pairs.length) return null;
	  var preDone=[]; for(var d0=0;d0<an.length;d0++) preDone.push(false);
	  for(var q0=0;q0<pairs.length;q0++){ preDone[pairs[q0]]=true; preDone[pairs[q0]+1]=true; }
	  // posiciones desarrolladas de las líneas de pliegue sobre chapa plana (DIN 6935)
	  var vDed=an.map(function(a){return din6935_v(180-a,ri,s);});   // negativo = descuento
	  var Ldev=0; for(var t=0;t<fl.length;t++) Ldev+=(fl[t]||0);
	  for(var t2=0;t2<vDed.length;t2++) Ldev+=vDed[t2];
	  function devX(k){ var x=0; for(var i2=0;i2<=k;i2++) x+=fl[i2]||0; for(var j=0;j<k;j++) x+=vDed[j]; return x+vDed[k]/2; }
	  var xg=(cal&&cal.xg)||0;
	  function Yfor(a){ var c=(state.angCorr&&state.angCorr[a])||0; var aF=a-sb-c; return cal.y90+cal.sign*(penetracion(aF,V)-penetracion(90-sb,V)); }
	  function cara(k){ return dr[k]<0?'cara ABAJO (dada vuelta)':'cara ARRIBA'; }
	  var pNom=curPunch?curPunch.name:'Recto', dNom=curDie?curDie.name:('V'+V+' 90°');
	  var endL=nodeLetter(fl.length);
	  var steps=[], paso=1;
	  for(var q=0;q<pairs.length;q++){
	    var i1=pairs[q], ib=i1+1;   // topeando del extremo final: primero el pliegue más lejos de ese borde (i1)
	    var L1=nodeLetter(i1+1), L2=nodeLetter(ib+1);
	    var X1=(Ldev-devX(i1)+xg), X2=(Ldev-devX(ib)+xg);
	    steps.push({paso:paso++,tipo:'pre',label:'Escalón '+L1+'-'+L2+' — pre-pliegue en '+L1+' a 135°',
	      hint:cara(i1)+' · tope: borde '+endL+' · chapa plana (X desarrollado)',
	      X:X1.toFixed(1), Y:Yfor(135).toFixed(2), punch:pNom, die:dNom});
	    steps.push({paso:paso++,tipo:'pre',label:'Pre-pliegue en '+L2+' a 135°',
	      hint:cara(ib)+' · tope: borde '+endL+' · chapa plana (X desarrollado)',
	      X:X2.toFixed(1), Y:Yfor(135).toFixed(2), punch:pNom, die:dNom});
	    steps.push({paso:paso++,tipo:'cierre',label:'Cierre de '+L2+' a 90°',
	      hint:'misma posición que el paso anterior — solo baja más la Y',
	      X:X2.toFixed(1), Y:Yfor(90).toFixed(2), punch:pNom, die:dNom});
	    steps.push({paso:paso++,tipo:'cierre',label:'Cierre de '+L1+' a 90°',
	      hint:cara(i1)+' · tope: contra el escalón recién cerrado en '+L2,
	      X:((fl[ib]||0)+xg).toFixed(1), Y:Yfor(90).toFixed(2), punch:pNom, die:dNom});
	  }
	  // el resto de los pliegues, con los escalones ya dados por hechos
	  var res=buscarOrden(fl,an,dr,V,s,preDone);
	  if(res.best){ var rs=res.best.steps;
	    for(var r2=0;r2<rs.length;r2++){ var st=rs[r2];
	      var man=(st.mx?'girá la pieza':'')+((st.mx&&st.my)?' y ':'')+(st.my?'dala vuelta':'');
	      steps.push({paso:paso++,tipo:'bend',
	        label:'Pliegue b'+(st.bend+1)+' — '+(an[st.bend]*(dr[st.bend]<0?-1:1))+'°',
	        hint:(st.ok?'':'⚠ '+(st.why||'choque')+' · ')+(man?man+' · ':'')+'tope: '+(st.gauge!=null?nodeLetter(st.gauge):'—'),
	        X:(st.X+xg).toFixed(1), Y:Yfor(an[st.bend]).toFixed(2), punch:pNom, die:dNom});
	    }
	  }
	  return steps;
	}

	/* ===== DESARROLLO (largo a cortar) ===== */
	function desarrollo(flanges,angles,ri,s){
	  var v=angles.map(function(a){return din6935_v(180-a,ri,s);});
	  var total=0; for(var i=0;i<flanges.length;i++) total+=(flanges[i]||0);
	  var sumv=0; for(var j=0;j<v.length;j++) sumv+=v[j];
	  return {dev:total+sumv, alas:total, descuento:sumv};
	}

	/* ===== ESTADO ===== */
	var state={ segs:[{len:50,ang:90},{len:80,ang:90},{len:50,ang:null}], plan:null, step:0, view:'machine', manual:false, manSeq:null, zoomDie:true, punchDown:false, angCorr:{}, xCorr:{} };
	function getCal(){ var r=localStorage.getItem('plegado_cal'); if(r){try{var c=JSON.parse(r); if(c.xg==null)c.xg=0; return c;}catch(e){}} return {y90:0,sign:1,xg:0}; }
	function setCal(c){ localStorage.setItem('plegado_cal',JSON.stringify(c)); }
	function curUtil(){ var V=parseFloat(document.getElementById('pp-V').value)||20; var riIn=document.getElementById('pp-ri').value; var ri=riIn===''?V*0.10:parseFloat(riIn); var s=parseFloat(document.getElementById('pp-s').value)||1; return {V:V,ri:ri,s:s}; }

	/* ===== TABLA DE TRAMOS (entrada tipo planilla) ===== */
	function focusLen(idx){
	  var el=document.querySelector('#pp-root input.len[data-i="'+idx+'"]');
	  if(el){ el.focus(); try{ el.select(); }catch(e){} }   // selecciona todo: al escribir, se reemplaza
	}
	function onLenKey(e){
	  var t=e.target, idx=+t.getAttribute('data-i');
	  function commit(){ state.segs[idx].len = t.value===''?null:parseFloat(t.value); }
	  if(e.keyCode===13 || e.key==='Enter'){
	    e.preventDefault(); commit();
	    if(idx===state.segs.length-1){
	      state.segs[idx].ang=90;
	      state.segs.push({len:null,ang:null});
	      renderSegs(); previewSetup(); focusLen(state.segs.length-1);
	    } else { renderSegs(); previewSetup(); focusLen(idx+1); }
	  } else if(e.keyCode===40 || e.key==='ArrowDown'){
	    e.preventDefault(); commit(); previewSetup();
	    if(idx<state.segs.length-1) focusLen(idx+1);
	  } else if(e.keyCode===38 || e.key==='ArrowUp'){
	    e.preventDefault(); commit(); previewSetup();
	    if(idx>0) focusLen(idx-1);
	  }
	}
	function focusAng(idx){ var el=document.querySelector('#pp-root input.ang[data-i="'+idx+'"]'); if(el){ el.focus(); try{ el.select(); }catch(e){} } }
	function onAngKey(e){
	  var t=e.target, idx=+t.getAttribute('data-i');
	  function commit(){ state.segs[idx].ang = t.value===''?null:parseFloat(t.value); }
	  var lastAng=state.segs.length-2;   // índice del último ángulo (la última ala no tiene)
	  if(e.keyCode===13 || e.key==='Enter'){
	    e.preventDefault(); commit(); previewSetup();
	    if(idx<lastAng) focusAng(idx+1); else focusAng(idx);
	  } else if(e.keyCode===40 || e.key==='ArrowDown'){ e.preventDefault(); commit(); previewSetup(); if(idx<lastAng) focusAng(idx+1); }
	  else if(e.keyCode===38 || e.key==='ArrowUp'){ e.preventDefault(); commit(); previewSetup(); if(idx>0) focusAng(idx-1); }
	}
	function renderSegs(){
	  var body=document.getElementById('pp-segBody'); body.innerHTML='';
	  for(var i=0;i<state.segs.length;i++){
	    var isLast=(i===state.segs.length-1);
	    var lv=(state.segs[i].len==null?'':state.segs[i].len);
	    var ang=isLast?'<td class="muted">— fin —</td>':'<td><input class="ang" type="text" inputmode="numeric" data-i="'+i+'" data-f="ang" value="'+(state.segs[i].ang==null?'':state.segs[i].ang)+'"></td>';
	    var tr=document.createElement('tr');
	    tr.innerHTML='<td class="seg-num">'+(i+1)+'</td><td><input class="len" type="text" inputmode="decimal" data-i="'+i+'" data-f="len" value="'+lv+'"></td>'+ang+'<td style="white-space:nowrap;"><button class="ghost" data-dup="'+i+'" style="padding:6px 9px;" title="Repetir esta ala (CY)">⧉</button>'+(state.segs.length>2?'<button class="ghost" data-del="'+i+'" style="padding:6px 9px;margin-left:4px;">✕</button>':'')+'</td>';
	    body.appendChild(tr);
	  }
	  var inps=body.querySelectorAll('input');
	  for(var j=0;j<inps.length;j++){
	    inps[j].addEventListener('change',function(e){ var t=e.target,idx=+t.getAttribute('data-i'),f=t.getAttribute('data-f'); state.segs[idx][f]=t.value===''?null:parseFloat(t.value); previewSetup(); });
	    inps[j].addEventListener('focus',function(e){ try{ e.target.select(); }catch(err){} });   // texto preseleccionado al entrar
	    if(/(^| )len( |$)/.test(inps[j].className)) inps[j].addEventListener('keydown',onLenKey);
	    if(/(^| )ang( |$)/.test(inps[j].className)) inps[j].addEventListener('keydown',onAngKey);
	  }
	  var dels=body.querySelectorAll('[data-del]');
	  for(var d=0;d<dels.length;d++){ dels[d].addEventListener('click',function(e){ var idx=+e.currentTarget.getAttribute('data-del'); state.segs.splice(idx,1); state.segs[state.segs.length-1].ang=null; renderSegs(); previewSetup(); }); }
	  // CY / copiar pliegue: duplica el ala (medida + ángulo) a continuación
	  var dups=body.querySelectorAll('[data-dup]');
	  for(var d2=0;d2<dups.length;d2++){ dups[d2].addEventListener('click',function(e){ var idx=+e.currentTarget.getAttribute('data-dup'); var s=state.segs[idx];
	    if(s.ang==null) s.ang=90;   // duplicó la última: la original pasa a intermedia con 90° (como "+ Agregar ala")
	    state.segs.splice(idx+1,0,{len:s.len,ang:s.ang});
	    state.segs[state.segs.length-1].ang=null; renderSegs(); previewSetup(); }); }
	}
	document.getElementById('pp-addSeg').addEventListener('click',function(){ var last=state.segs[state.segs.length-1]; if(last.ang==null)last.ang=90; state.segs.push({len:null,ang:null,dir:1}); renderSegs(); previewSetup(); focusLen(state.segs.length-1); });

	/* ===== DIBUJO DEL PERFIL ===== */
	function partPoints(flanges,angles,dirs){
	  var pts=[{x:0,y:0}],dir=0,x=0,y=0,segs=[];
	  for(var i=0;i<flanges.length;i++){ var nx=x+(flanges[i]||0)*Math.cos(dir*DEG),ny=y+(flanges[i]||0)*Math.sin(dir*DEG); segs.push({x1:x,y1:y,x2:nx,y2:ny}); pts.push({x:nx,y:ny}); x=nx;y=ny; if(i<angles.length) dir+=dirs[i]*(180-angles[i]); }
	  return {pts:pts,segs:segs};
	}
	function fitDraw(svgId,segs,pts,labelFn,nodeFn,W,H,pad){
	  var minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
	  for(var q=0;q<pts.length;q++){ if(pts[q].x<minx)minx=pts[q].x; if(pts[q].y<miny)miny=pts[q].y; if(pts[q].x>maxx)maxx=pts[q].x; if(pts[q].y>maxy)maxy=pts[q].y; }
	  var sc=Math.min((W-2*pad)/Math.max(1,maxx-minx),(H-2*pad)/Math.max(1,maxy-miny));
	  function TX(x){return pad+(x-minx)*sc;} function TY(y){return H-(pad+(y-miny)*sc);}
	  var svg='';
	  for(var i=0;i<segs.length;i++){ var d=segs[i]; svg+='<line x1="'+TX(d.x1).toFixed(1)+'" y1="'+TY(d.y1).toFixed(1)+'" x2="'+TX(d.x2).toFixed(1)+'" y2="'+TY(d.y2).toFixed(1)+'" stroke="#5b7a9e" stroke-width="5" stroke-linecap="round"/>'; if(labelFn){ var mx=(d.x1+d.x2)/2,my=(d.y1+d.y2)/2; svg+='<text x="'+TX(mx).toFixed(1)+'" y="'+(TY(my)+16).toFixed(1)+'" fill="#8aa0bd" font-size="12" text-anchor="middle">'+labelFn(i)+'</text>'; } }
	  if(nodeFn) svg+=nodeFn(TX,TY,pts);
	  document.getElementById(svgId).innerHTML=svg;
	}
	function drawFinished(svgId,fl,an,dr){
	  var g=partPoints(fl,an,dr);
	  // orientar APAISADO: si la pieza es más alta que ancha, la roto 90°
	  var bx0=1e9,by0=1e9,bx1=-1e9,by1=-1e9;
	  for(var q=0;q<g.pts.length;q++){ var pp=g.pts[q]; if(pp.x<bx0)bx0=pp.x; if(pp.y<by0)by0=pp.y; if(pp.x>bx1)bx1=pp.x; if(pp.y>by1)by1=pp.y; }
	  var rot90=((by1-by0) > (bx1-bx0)*1.05);
	  function tr(x,y){ return rot90?{x:y,y:-x}:{x:x,y:y}; }
	  var P2=g.pts.map(function(p){return tr(p.x,p.y);});
	  var segs2=g.segs.map(function(sg){ var a=tr(sg.x1,sg.y1),b=tr(sg.x2,sg.y2); return {x1:a.x,y1:a.y,x2:b.x,y2:b.y}; });
	  fitDraw(svgId,segs2,P2,function(i){return (fl[i]||0);},function(TX,TY,pts){
	    var s='';
	    // ángulo (con signo), gris, al costado del pliegue
	    for(var b=0;b<an.length;b++){ var vp=pts[b+1];
	      s+='<text x="'+(TX(vp.x)+15).toFixed(1)+'" y="'+(TY(vp.y)+4).toFixed(1)+'" fill="#9fb3cf" font-size="11" text-anchor="middle">'+(an[b]*(dr[b]<0?-1:1))+'°</text>';
	    }
	    // letras de nodo SIN círculo, naranja furioso, apenas separadas del nodo
	    for(var i=0;i<pts.length;i++){ var vp=pts[i];
	      s+='<text x="'+(TX(vp.x)-9).toFixed(1)+'" y="'+(TY(vp.y)-7).toFixed(1)+'" fill="#ff5a00" font-size="16" font-weight="800" text-anchor="middle">'+nodeLetter(i)+'</text>';
	    }
	    return s; },460,190,26);
	}
	function nodeLetter(i){ return String.fromCharCode(65+(i%26)); }

	/* ===== EXPORTAR DXF: contorno de la chapa con espesor (cara int. ri, cara ext. ri+s) ===== */
	/* Construye el contorno de la chapa como ELEMENTOS geométricos exactos:
	   cada tramo recto -> {t:'L',a,b}; cada pliegue -> arco de circunferencia
	   {t:'A',C,R,a0,a1,phi} con centro, radio y ángulos reales (no poligonizado).
	   Dos caras (A/B) offset ±s/2 de la fibra neutra + dos tapas en los extremos. */
	function buildSheetElements(fl,an,dr,ri,s){
	  var Rm=ri+s/2, half=s/2;
	  function U(a){return {x:Math.cos(a*DEG),y:Math.sin(a*DEG)};}
	  var dirs=[], d=0;
	  for(var i=0;i<fl.length;i++){ dirs.push(d); if(i<an.length) d+=dr[i]*(180-an[i]); }
	  // nodos de la fibra neutra (vértices ideales)
	  var node=[{x:0,y:0}], x=0,y=0;
	  for(var i=0;i<fl.length;i++){ x+=fl[i]*Math.cos(dirs[i]*DEG); y+=fl[i]*Math.sin(dirs[i]*DEG); node.push({x:x,y:y}); }
	  // datos de cada pliegue: puntos de tangencia, centro del arco, ángulos
	  var bd=[];
	  for(var i=0;i<an.length;i++){
	    var phi=dr[i]*(180-an[i]);                 // giro exterior con signo
	    var t=Rm*Math.tan(Math.abs(phi)/2*DEG);     // largo de tangente
	    var uin=U(dirs[i]), uout=U(dirs[i+1]);
	    var Tin={x:node[i+1].x-t*uin.x, y:node[i+1].y-t*uin.y};
	    var sg=(phi>0?1:-1);
	    var nIn={x:-uin.y*sg, y:uin.x*sg};          // normal hacia el centro del arco
	    var C={x:Tin.x+Rm*nIn.x, y:Tin.y+Rm*nIn.y};
	    var Tout={x:node[i+1].x+t*uout.x, y:node[i+1].y+t*uout.y};
	    var a0=Math.atan2(Tin.y-C.y,Tin.x-C.x)/DEG, a1=Math.atan2(Tout.y-C.y,Tout.x-C.x)/DEG;
	    bd.push({phi:phi,sg:sg,C:C,a0:a0,a1:a1});
	  }
	  function fp(C,R,a){ return {x:C.x+R*Math.cos(a*DEG), y:C.y+R*Math.sin(a*DEG)}; }
	  function normalL(k){ var u=U(dirs[k]); return {x:-u.y,y:u.x}; }   // normal izquierda del ala
	  var elemsA=[], elemsB=[];
	  var nl0=normalL(0);
	  var Astart={x:node[0].x+half*nl0.x, y:node[0].y+half*nl0.y};
	  var Bstart={x:node[0].x-half*nl0.x, y:node[0].y-half*nl0.y};
	  var curA=Astart, curB=Bstart;
	  for(var i=0;i<fl.length;i++){
	    if(i<an.length){
	      var b=bd[i]; var Ra=Rm-b.sg*half, Rb=Rm+b.sg*half;   // cara A: cóncava o convexa según giro
	      var aInA=fp(b.C,Ra,b.a0), aOutA=fp(b.C,Ra,b.a1);
	      var aInB=fp(b.C,Rb,b.a0), aOutB=fp(b.C,Rb,b.a1);
	      elemsA.push({t:'L',a:curA,b:aInA});
	      elemsA.push({t:'A',C:b.C,R:Ra,a0:b.a0,a1:b.a1,phi:b.phi});
	      elemsB.push({t:'L',a:curB,b:aInB});
	      elemsB.push({t:'A',C:b.C,R:Rb,a0:b.a0,a1:b.a1,phi:b.phi});
	      curA=aOutA; curB=aOutB;
	    } else {
	      var nlN=normalL(i);
	      var Aend={x:node[i+1].x+half*nlN.x, y:node[i+1].y+half*nlN.y};
	      var Bend={x:node[i+1].x-half*nlN.x, y:node[i+1].y-half*nlN.y};
	      elemsA.push({t:'L',a:curA,b:Aend});
	      elemsB.push({t:'L',a:curB,b:Bend});
	      curA=Aend; curB=Bend;
	    }
	  }
	  // contorno cerrado: cara A + tapa final + cara B + tapa inicial (entidades sueltas, orden no importa)
	  return elemsA.concat([{t:'L',a:curA,b:curB}], elemsB, [{t:'L',a:Bstart,b:Astart}]);
	}
	function elemsToDXF(elems){
	  var d='0\nSECTION\n2\nENTITIES\n';
	  for(var i=0;i<elems.length;i++){ var e=elems[i];
	    if(e.t==='L'){
	      d+='0\nLINE\n8\nPIEZA\n62\n5\n10\n'+e.a.x.toFixed(4)+'\n20\n'+e.a.y.toFixed(4)+'\n11\n'+e.b.x.toFixed(4)+'\n21\n'+e.b.y.toFixed(4)+'\n';
	    } else {
	      // DXF: ARC siempre CCW de 50 a 51. Si el barrido es horario (phi<0) invierto extremos.
	      var s0=e.a0, s1=e.a1; if(e.phi<0){ var tmp=s0; s0=e.a1; s1=e.a0; }
	      s0=((s0%360)+360)%360; s1=((s1%360)+360)%360;
	      d+='0\nARC\n8\nPIEZA\n62\n5\n10\n'+e.C.x.toFixed(4)+'\n20\n'+e.C.y.toFixed(4)+'\n40\n'+e.R.toFixed(4)+'\n50\n'+s0.toFixed(4)+'\n51\n'+s1.toFixed(4)+'\n';
	    }
	  }
	  return d+'0\nENDSEC\n0\nEOF\n';
	}
	function exportDXF(){
	  var fl=state.segs.map(function(x){return x.len||0;}); var an=[],dr=[];
	  for(var i=0;i<state.segs.length-1;i++){ var a=(state.segs[i].ang==null?90:state.segs[i].ang); an.push(Math.abs(a)); dr.push(a<0?-1:1); }
	  if(fl.length<2){ alert('Cargá al menos 2 alas.'); return; }
	  var ut=curUtil();
	  var dxf=elemsToDXF(buildSheetElements(fl,an,dr,ut.ri,ut.s));
	  // nombre sugerido: referencia del pedido > nombre por medidas > genérico
	  var refEl=document.getElementById('pp-ped-ref');
	  var defaultName=(refEl&&refEl.value.replace(/^\s+|\s+$/g,'')) || partDefaultName(state.segs) || 'pieza_corte';
	  defaultName=defaultName.replace(/[\/\\:*?"<>|]/g,'_');
	  if(window.showSaveFilePicker){
	    // navegadores modernos: diálogo nativo del SO (elegís carpeta y nombre)
	    window.showSaveFilePicker({
	      suggestedName: defaultName+'.dxf',
	      types:[{description:'Archivo DXF', accept:{'application/dxf':['.dxf']}}]
	    }).then(function(fileHandle){ return fileHandle.createWritable(); })
	      .then(function(writable){ return writable.write(dxf).then(function(){ return writable.close(); }); })
	      .catch(function(e){ if(e.name!=='AbortError') alert('Error al guardar: '+e.message); });
	  } else {
	    // iOS 12 Safari y navegadores sin File System Access API: el nombre se pide con prompt
	    var nombre=prompt('Nombre del archivo DXF:',defaultName);
	    if(nombre===null) return;   // canceló
	    if(!nombre) nombre=defaultName;
	    nombre=nombre.replace(/\.dxf$/i,'')+'.dxf';
	    var a=document.createElement('a');
	    a.href='data:application/dxf;charset=utf-8,'+encodeURIComponent(dxf);
	    a.download=nombre;
	    document.body.appendChild(a); a.click(); setTimeout(function(){ document.body.removeChild(a); }, 200);
	  }
	}
	function previewSetup(){
	  var fl=state.segs.map(function(x){return x.len;}); var an=[],dr=[];
	  for(var i=0;i<state.segs.length-1;i++){ var a=(state.segs[i].ang==null?90:state.segs[i].ang); an.push(Math.abs(a)); dr.push(a<0?-1:1); }
	  drawFinished('pp-previewPart',fl,an,dr);
	  // largo a cortar en vivo
	  var ut=curUtil(); var flv=fl.map(function(x){return x||0;}); var anv=an;
	  var ang2=[]; for(var k=0;k<state.segs.length-1;k++) ang2.push(state.segs[k].ang||90);
	  var d=desarrollo(flv,ang2,ut.ri,ut.s);
	  document.getElementById('pp-devVal').textContent = isFinite(d.dev)? d.dev.toFixed(1)+' mm' : '—';
	  document.getElementById('pp-devSub').textContent = 'suma de alas '+d.alas.toFixed(0)+' mm  ·  descuento por pliegues '+d.descuento.toFixed(1)+' mm';
	}

	function drawPartProgress(step){
	  var p=state.plan, done=[]; for(var i=0;i<p.angles.length;i++) done.push(false);
	  for(var j=0;j<step;j++) done[p.steps[j].bend]=true;
	  var nb=p.steps[step].bend;
	  var eff=[]; for(var a=0;a<p.angles.length;a++) eff.push(done[a]?p.angles[a]:180);
	  var g=partPoints(p.flanges,eff,p.dirs);
	  fitDraw('pp-machine',g.segs,g.pts,null,function(TX,TY,pts){ var s=''; for(var b=0;b<p.angles.length;b++){ var vp=pts[b+1]; var isNext=(b===nb),isDone=done[b]; var col=isNext?'#8b5cf6':(isDone?'#19b877':'#6e8aae'); s+='<circle cx="'+TX(vp.x).toFixed(1)+'" cy="'+TY(vp.y).toFixed(1)+'" r="'+(isNext?9:5)+'" fill="'+col+'"/>'; if(isNext) s+='<text x="'+TX(vp.x).toFixed(1)+'" y="'+(TY(vp.y)-13).toFixed(1)+'" fill="#6d4bc0" font-size="13" text-anchor="middle">próximo: '+p.angles[b]+'°</text>'; else if(isDone) s+='<text x="'+TX(vp.x).toFixed(1)+'" y="'+(TY(vp.y)-12).toFixed(1)+'" fill="#19a86c" font-size="12" text-anchor="middle">'+p.angles[b]+'°</text>'; } return s; },460,300,30);
	}

	/* ===== PLAN ===== */
	function buildPlan(){
	  var s=parseFloat(document.getElementById('pp-s').value), L=parseFloat(document.getElementById('pp-L').value);
	  var sigma=parseFloat(document.getElementById('pp-Rm').value)||45; var RmN=sigma*9.81;   // kg/mm² (como el SIGMA del Cybelec) -> N/mm²
	  var V=parseFloat(document.getElementById('pp-V').value); var riIn=document.getElementById('pp-ri').value; var ri=riIn===''?V*0.10:parseFloat(riIn);
	  var sb=parseFloat(document.getElementById('pp-sb').value)||0; var cal=getCal();
	  var flanges=state.segs.map(function(x){return x.len;}); var angles=[],dirs=[];
	  for(var i=0;i<state.segs.length-1;i++){ var a=(state.segs[i].ang==null?90:state.segs[i].ang); angles.push(Math.abs(a)); dirs.push(a<0?-1:1); }
	  var d=desarrollo(flanges.map(function(x){return x||0;}),angles,ri,s);
	  // corrección de ángulo empírica (flujo Cybelec): si midió alfa real ≠ objetivo, formar más profundo/liviano
	  function Yfor(alpha){ var corr=(state.angCorr&&state.angCorr[alpha])||0; var aF=alpha-sb-corr; return cal.y90+cal.sign*(penetracion(aF,V)-penetracion(90-sb,V)); }
	  var dr0=dieRot(); var minA=Math.max(curPunch?curPunch.minA:88, dr0?dr0.minA:88);
	  function enrich(st){
	    var warns=[]; if(!st.ok&&st.why) warns.push(st.why);
	    if(st.bend!=null&&st.alpha<minA) warns.push('ángulo '+st.alpha+'° más cerrado que el mínimo de estos útiles ('+minA+'°)');
	    if(st.bend!=null){ var sens=sensibilidad(st.alpha-sb,V); if(sens<0.05) warns.push('sensibilidad baja ('+sens.toFixed(3)+' mm/°): conviene una V más ancha'); }
	    // X final = geométrica + corrección global de máquina + corrección fina de este pliegue
	    var xFine=(st.bend!=null&&state.xCorr&&state.xCorr[st.bend])||0;
	    return {orderNo:st.order, bendIndex:st.bend, alpha:st.alpha, Xraw:st.X, X:(st.bend!=null?st.X+(cal.xg||0)+xFine:st.X), Y:(st.bend!=null?Yfor(st.alpha):0), mx:st.mx, my:st.my, ok:st.ok, warns:warns, gaugeNode:st.gauge};
	  }
	  var steps, cerebro, wPlan=null, wTipo=null;
	  if(state.manual && state.manSeq){
	    steps=simulateManual(flanges,angles,dirs,state.manSeq,V,s).steps.map(enrich);
	    var col=0; for(var i=0;i<steps.length;i++) if(!steps[i].ok) col++;
	    cerebro={manual:true, collisions:col};
	  } else if(state.keepOrder && state.keepOrder.length===angles.length){
	    // "Volver a la secuencia": mantener el SETUP completo de cada paso — orden de
	    // pliegues Y nodo de tope (la orientación sale sola del nodo elegido) — y solo
	    // recalcular X/Y con las medidas nuevas. Si un paso ya no se puede, queda ⚠.
	    var rm=simulateManual(flanges,angles,dirs,state.keepOrder,V,s);
	    steps=rm.steps.map(enrich);
	    var kcol=0,kflips=0,kgiras=0,kpm=null,kpy=null;
	    for(var ki=0;ki<rm.steps.length;ki++){ var ks=rm.steps[ki];
	      if(!ks.ok) kcol++;
	      if(kpm!==null&&ks.mx!==kpm) kgiras++;
	      if(kpy!==null&&ks.my!==kpy) kflips++;
	      kpm=ks.mx; kpy=ks.my; }
	    cerebro={manual:false, keepOrder:true, tried:1, feasibleCount:kcol===0?1:0, collisions:kcol, manips:kflips+kgiras, flips:kflips, giras:kgiras, opViol:0};
	  } else {
	    state.keepOrder=null;
	    var res=buscarOrden(flanges,angles,dirs,V,s);
	    steps=res.best.steps.map(enrich);
	    cerebro={manual:false, keepOrder:false, tried:res.tried, feasibleCount:res.feasibleCount, collisions:res.best.collisions, manips:res.best.manips, flips:res.best.flips, giras:res.best.giras, opViol:res.best.opViol};
	    // Técnica W solo si TODOS los órdenes chocan (best tiene el mínimo de choques):
	    // apoyo inestable o poco sostén del operario NO justifican la técnica W.
	    if(!state.manual&&res.best.collisions>0){
	      wPlan=tryWBend(flanges,angles,dirs,V,ri,s,cal,sb); wTipo=wPlan?'w':null;
	      if(!wPlan){ wPlan=tryJoggle(flanges,angles,dirs,V,ri,s,cal,sb); wTipo=wPlan?'escalon':null; }
	    }
	  }
	  return {s:s,L:L,V:V,ri:ri,sb:sb,minA:minA,manual:state.manual,nbends:angles.length,nnodes:flanges.length+1,punch:(curPunch?curPunch.name:''),die:(curDie?curDie.name:''),flanges:flanges,angles:angles,dirs:dirs,devel:d.dev,totalFlat:d.alas,steps:steps,ton:tonelaje(L,s,RmN,V),cal:cal,cerebro:cerebro,wPlan:wPlan,wTipo:wTipo};
	}

	/* ===== RESUMEN ===== */
	function line(k,v){ return '<div class="summary-line"><span class="muted">'+k+'</span><span class="big">'+v+'</span></div>'; }
	function showResult(){
	  var p=state.plan, cb=p.cerebro, man=p.manual;
	  var res=line('Largo a cortar (desarrollo)',p.devel.toFixed(1)+' mm')+
	    line('Descuento total por pliegues',(p.devel-p.totalFlat).toFixed(1)+' mm')+
	    line('Tonelaje estimado',p.ton.ton.toFixed(1)+' ton ('+(p.ton.ton/(p.L/1000)).toFixed(1)+' ton/m)');
	  if(!man) res+=line('Órdenes evaluados',cb.tried+'  ('+cb.feasibleCount+' buenos)')+line('Vueltas / giros',cb.flips+' vuelta(s), '+cb.giras+' giro(s)');
	  res+=line('Cota Y a 90° (calibración)',p.cal.y90+' mm');
	  if(state.angCorr){ for(var ac in state.angCorr){ if(state.angCorr.hasOwnProperty(ac)) res+=line('Corrección empírica '+ac+'°',((-state.angCorr[ac])>0?'+':'')+(-state.angCorr[ac]).toFixed(1)+'° de formado'); } }
	  if(p.cal.xg) res+=line('Corrección X global',(p.cal.xg>0?'+':'')+p.cal.xg.toFixed(2)+' mm');
	  if(state.xCorr){ for(var xc in state.xCorr){ if(state.xCorr.hasOwnProperty(xc)) res+=line('Corrección X pliegue b'+(+xc+1),(state.xCorr[xc]>0?'+':'')+state.xCorr[xc].toFixed(2)+' mm'); } }
	  document.getElementById('pp-resumen').innerHTML=res;
	  drawFinished('pp-resultPart',p.flanges,p.angles,p.dirs);
	  var useW=!!(state.useW&&p.wPlan);
	  document.getElementById('pp-seqTitle').textContent = useW?(p.wTipo==='escalon'?'Secuencia (técnica de escalón)':'Secuencia (técnica W)'):(man?'Secuencia (manual)':(cb.keepOrder?'Secuencia (orden mantenido)':'Secuencia (automática)'));
	  document.getElementById('pp-btnManual').textContent = man?'↩︎ Volver a automático':'✏️ Editar a mano';
	  document.getElementById('pp-btnManual').style.display = useW?'none':'';
	  document.getElementById('pp-seqBody').closest('table').style.display = useW?'none':'';
	  document.getElementById('pp-manualHint').style.display = man?'block':'none';
	  // opciones de los desplegables
	  function bendOpts(sel){ var h=''; for(var b=0;b<p.nbends;b++) h+='<option value="'+b+'"'+(b===sel?' selected':'')+'>b'+(b+1)+'</option>'; return h; }
	  function nodeOpts(sel){ var h=''; for(var n=0;n<p.nnodes;n++) h+='<option value="'+n+'"'+(n===sel?' selected':'')+'>'+nodeLetter(n)+'</option>'; return h; }
	  var sb=document.getElementById('pp-seqBody'); sb.innerHTML='';
	  for(var i=0;i<p.steps.length;i++){ var st=p.steps[i]; var tr=document.createElement('tr');
	    var asig=(st.bendIndex!=null)?(st.alpha*(p.dirs[st.bendIndex]<0?-1:1))+'°':'—';
	    var estado = st.ok ? ((st.mx?'gira ':'')+(st.my?'voltea':'')||'✓') : '⚠';
	    var cP, cN;
	    if(man){ cP='<select class="mansel" data-row="'+i+'" data-f="bend">'+bendOpts(st.bendIndex)+'</select>'; cN='<select class="mansel" data-row="'+i+'" data-f="node">'+nodeOpts(st.gaugeNode)+'</select>'; }
	    else { cP='b'+(st.bendIndex+1); cN='<b style="color:#19a86c;">'+(st.gaugeNode!=null?nodeLetter(st.gaugeNode):'—')+'</b>'; }
	    tr.innerHTML='<td><b>'+(i+1)+'</b></td><td>'+cP+'</td><td>'+asig+'</td><td>'+cN+'</td><td>'+st.X.toFixed(1)+'</td><td>'+st.Y.toFixed(2)+'</td><td '+(st.ok?'':'style="color:#b23560"')+'>'+estado+'</td>';
	    sb.appendChild(tr); }
	  if(man){ var sels=sb.querySelectorAll('.mansel'); for(var s2=0;s2<sels.length;s2++){ sels[s2].addEventListener('change',onManSel); } }
	  var wd=document.getElementById('pp-warnings'), wh='';
	  if(!useW){
	    if(cb.collisions>0) wh+='<div class="warn bad">⚠︎ '+cb.collisions+' paso(s) con choque (marcados con ⚠ abajo). Quizás haga falta otro útil o partir la pieza.</div>';
	    if(!man && cb.opViol>0) wh+='<div class="warn">⚠︎ '+cb.opViol+' paso(s) dejan poco de dónde sostener la pieza del lado del operario. Probá el modo manual o revisá las medidas.</div>';
	    if(!wh) wh='<div class="muted"><span class="ok-pill">✓</span> Secuencia sin choques y sostenible.</div>';
	  }
	  wd.innerHTML=wh;
	  var wc=document.getElementById('pp-wbendCard');
	  if(p.wPlan){
	    var bC=useW?'#19a86c':'#e89c1a', bg=useW?'#eefcf5':'#fff8ec', tc=useW?'#0c7a4d':'#a56200';
	    var isEsc=(p.wTipo==='escalon');
	    var tecNom=isEsc?'Técnica de escalón — pre-plegado a 135°':'Técnica W — plegado en etapas';
	    var tecDesc=isEsc
	      ?'La secuencia directa choca en '+cb.collisions+' paso(s). Los escalones cortos no salen directo: se <b>pre-pliegan los dos pliegues del escalón a 135°</b> con la chapa todavía plana, y se cierran a 90° después. El resto de los pliegues se secuencia normal con los escalones ya hechos.'
	      :'La secuencia directa choca en '+cb.collisions+' paso(s). La pieza se puede fabricar con la <b>técnica W</b>: pliegue provisorio en el centro del alma, luego las alas normales, y finalmente se aplasta el provisorio sobre el punzón plano → queda el perfil U final.';
	    var wh2='<div style="background:'+bg+';border:2px solid '+bC+';border-radius:10px;padding:14px 14px 10px;margin-top:14px;">'
	      +'<div style="font-weight:800;font-size:15px;color:'+tc+';margin-bottom:6px;">'+(useW?'✔ '+tecNom.split(' — ')[0]+' — secuencia activa':'⚠ '+tecNom)+'</div>'
	      +(useW
	        ?'<div class="muted" style="margin-bottom:10px;font-size:13px;">Esta es la secuencia a ejecutar. "Empezar a plegar" recorre estos pasos.</div>'
	        :'<div class="muted" style="margin-bottom:10px;font-size:13px;">'+tecDesc+'</div>')
	      +'<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr style="background:'+(useW?'#d7f3e6':'#f5e9d0')+';">'
	      +'<th style="padding:5px 7px;text-align:left;">Paso</th><th style="padding:5px 7px;text-align:left;">Operación</th>'
	      +'<th style="padding:5px 7px;text-align:right;">X (mm)</th><th style="padding:5px 7px;text-align:right;">Y</th>'
	      +'<th style="padding:5px 7px;text-align:left;">Punzón</th><th style="padding:5px 7px;text-align:left;">Matriz</th>'
	      +'</tr></thead><tbody>';
	    for(var ww=0;ww<p.wPlan.length;ww++){
	      var ws=p.wPlan[ww];
	      wh2+='<tr style="border-top:1px solid '+(useW?'#bfe8d4':'#e8d9b8')+';">'
	        +'<td style="padding:5px 7px;"><b>'+ws.paso+'</b></td>'
	        +'<td style="padding:5px 7px;">'+ws.label+'<br><span style="color:#888;font-size:11px;">'+ws.hint+'</span></td>'
	        +'<td style="padding:5px 7px;text-align:right;">'+ws.X+'</td>'
	        +'<td style="padding:5px 7px;text-align:right;">'+ws.Y+'</td>'
	        +'<td style="padding:5px 7px;font-size:11px;">'+ws.punch+'</td>'
	        +'<td style="padding:5px 7px;font-size:11px;">'+ws.die+'</td>'
	        +'</tr>';
	    }
	    wh2+='</tbody></table>'
	      +'<div class="btnbar" style="margin-top:10px;">'
	      +(useW
	        ?'<button class="ghost" id="pp-btnNoW" type="button" style="flex:1 1 auto;padding:9px 12px;">↩ Volver a la secuencia directa</button>'
	        :'<button id="pp-btnUseW" type="button" style="flex:1 1 auto;padding:10px 12px;">✔ Usar esta técnica — armar la secuencia</button>')
	      +'</div></div>';
	    wc.innerHTML=wh2; wc.style.display='block';
	    var bw=document.getElementById('pp-btnUseW'); if(bw) bw.addEventListener('click',function(){ state.useW=true; state.step=0; showResult(); });
	    var bn=document.getElementById('pp-btnNoW'); if(bn) bn.addEventListener('click',function(){ state.useW=false; state.step=0; showResult(); });
	  } else { wc.innerHTML=''; wc.style.display='none'; }
	  show('pp-result');
	}

	/* ===== CILINDRADO (BUMP BENDING) ===== */
	function buildCilindrado(){
	  var R=parseFloat(document.getElementById('pp-cilR').value);
	  var O=parseFloat(document.getElementById('pp-cilO').value);
	  var Qtgt=parseFloat(document.getElementById('pp-cilQ').value)||15;
	  var V=parseFloat(document.getElementById('pp-V').value)||20;
	  var sb=parseFloat(document.getElementById('pp-sb').value)||0;
	  var cal=getCal();
	  if(!R||!O||R<5||O<1||O>360) return null;
	  var N=Math.ceil(O/Qtgt); if(N<1) N=1;
	  var Q=O/N; var alpha=180-Q;
	  var AL=(O/180)*Math.PI*R; var P=AL/N; var Vopt=P*2;
	  var aF=alpha-sb; var Y=cal.y90+cal.sign*(penetracion(aF,V)-penetracion(90-sb,V));
	  var bestDie=null,bestV=null,bestDiff=1e9;
	  for(var m=0;m<TOOLS.matrices.length;m++){ var mat=TOOLS.matrices[m]; if(mat.rotations){ for(var r=0;r<mat.rotations.length;r++){ var mv=mat.rotations[r].V||0; var diff=Math.abs(mv-Vopt); if(mv>0&&diff<bestDiff){bestDiff=diff;bestDie=mat;bestV=mv;} } } }
	  var steps=[]; var xg=(cal.xg||0);
	  for(var i=0;i<N;i++) steps.push({paso:i+1,X:((i+0.5)*P+xg).toFixed(1),Y:Y.toFixed(2)});
	  return {R:R,O:O,N:N,Q:Q,alpha:alpha,AL:AL,P:P,Vopt:Vopt,Y:Y,bestDie:bestDie,bestV:bestV,steps:steps};
	}
	function showCilindrado(){
	  var c=buildCilindrado();
	  var el=document.getElementById('pp-cilResult');
	  if(!c){el.innerHTML='<div class="warn bad" style="margin-top:8px;">Revisar los datos ingresados.</div>';return;}
	  var dieNote=c.bestDie?c.bestDie.name+' (V='+c.bestV+'mm — disponible)':'V≈'+c.Vopt.toFixed(0)+'mm (no disponible — elegir la más cercana)';
	  var warn=c.P<8?'<div class="warn" style="margin-top:6px;">⚠ Avance muy pequeño (P='+c.P.toFixed(1)+'mm). Reducí Q o usá un dado más chico.</div>':'';
	  if(c.bestDie && c.bestV < c.Vopt*0.6){
	    var Palt=c.bestV/2, Nalt=Math.ceil(c.AL/Palt), Qalt=(c.O/Nalt);
	    warn+='<div class="warn" style="margin-top:6px;">⚠ El dado disponible (V='+c.bestV+'mm) es más chico que el ideal (V≈'+c.Vopt.toFixed(0)+'mm). Con ese dado, avance máximo P='+Palt.toFixed(1)+'mm → necesitarías <b>N='+Nalt+' golpes</b> de Q='+Qalt.toFixed(1)+'°.</div>';
	  }
	  var h='<div class="card" style="background:#f0f8ff;border-color:#60a5fa;margin-top:10px;">'
	    +'<div style="font-weight:800;font-size:15px;color:#1d4ed8;margin-bottom:8px;">⌒ Plan de cilindrado</div>'
	    +'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;font-size:13px;margin-bottom:10px;">'
	    +'<div><span class="muted">Radio:</span> <b>'+c.R+' mm</b></div>'
	    +'<div><span class="muted">Ángulo total:</span> <b>'+c.O+'°</b></div>'
	    +'<div><span class="muted">Golpes N:</span> <b>'+c.N+'</b></div>'
	    +'<div><span class="muted">Q por golpe:</span> <b>'+c.Q.toFixed(2)+'°</b></div>'
	    +'<div><span class="muted">α por pliegue:</span> <b>'+c.alpha.toFixed(2)+'°</b></div>'
	    +'<div><span class="muted">Arco AL:</span> <b>'+c.AL.toFixed(1)+' mm</b></div>'
	    +'<div><span class="muted">Avance P:</span> <b>'+c.P.toFixed(2)+' mm</b></div>'
	    +'<div><span class="muted">Cota Y:</span> <b>'+c.Y.toFixed(2)+' mm</b></div>'
	    +'<div style="grid-column:1/-1"><span class="muted">Dado óptimo (V≈'+c.Vopt.toFixed(0)+'mm):</span> <b>'+dieNote+'</b></div>'
	    +'</div>'
	    +'<p class="muted" style="font-size:12px;margin:0 0 10px;">Cota Y igual en todos los golpes. Avanzar tope X en <b>'+c.P.toFixed(2)+' mm</b> entre cada golpe (o mover la pieza manualmente).</p>'
	    +'<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr style="background:#dbeafe;">'
	    +'<th style="padding:5px 7px;text-align:center;">Paso</th>'
	    +'<th style="padding:5px 7px;text-align:right;">Tope X (mm)</th>'
	    +'<th style="padding:5px 7px;text-align:right;">Cota Y (mm)</th>'
	    +'</tr></thead><tbody>';
	  for(var i=0;i<c.steps.length;i++){
	    var st=c.steps[i];
	    h+='<tr style="border-top:1px solid #bfdbfe;">'
	      +'<td style="padding:4px 7px;text-align:center;"><b>'+st.paso+'</b></td>'
	      +'<td style="padding:4px 7px;text-align:right;">'+st.X+'</td>'
	      +'<td style="padding:4px 7px;text-align:right;">'+st.Y+'</td>'
	      +'</tr>';
	  }
	  h+='</tbody></table></div>'+warn;
	  el.innerHTML=h;
	}

	function onManSel(e){ var row=+e.target.getAttribute('data-row'), f=e.target.getAttribute('data-f'); state.manSeq[row][f]=+e.target.value; state.plan=buildPlan(); showResult(); }
	function toggleManual(){
	  if(!state.manual){
	    // pasar a manual: arrancar pre-cargado con la secuencia actual
	    state.manSeq=state.plan.steps.map(function(st){ return {bend:st.bendIndex, node:st.gaugeNode}; });
	    state.manual=true;
	  } else { state.manual=false; state.manSeq=null; }
	  state.useW=false;
	  state.plan=buildPlan(); showResult();
	}

	/* ===== SIMULACIÓN: dos estados a la vez (ahora + después), sin movimiento ===== */
	function machineGeom(step,foldFrac){
	  var p=state.plan, st=p.steps[step], bi=st.bendIndex;
	  var done=[]; for(var i=0;i<p.angles.length;i++) done.push(false);
	  for(var j=0;j<step;j++) done[p.steps[j].bendIndex]=true;
	  var pl=place(p.flanges,p.angles,p.dirs,done,bi,st.mx,st.my,p.s);
	  var pen=penClamp(st.alpha,p.V);
	  // La matriz y el punzón MASTICAN la chapa: el vértice baja a la V y AMBOS brazos SUBEN
	  // siempre (el punzón baja al centro de la V), cada uno la mitad del ángulo exterior.
	  // El signo del giro de cada brazo depende del lado del vértice donde quedó tras el espejado
	  // mx de place(): el brazo a -x gira horario, el de +x antihorario. Con mx los índices bajos
	  // (idx<=bi) quedan a +x, así que se decide por geometría colocada, no por índice ni por el
	  // signo del giro del perfil (eso fallaba con la pieza girada: ambos brazos caían).
	  var half=foldFrac*(180-st.alpha)/2;
	  var sideL=(pl.P[bi].x<=pl.P[bi+1].x)?-1:1, leftAng=sideL*half, rightAng=-sideL*half;
	  var P=pl.P.map(function(pt,idx){
	    var a = (idx<=bi)? leftAng : (idx>=bi+2? rightAng : 0);    // ambos brazos suben; el vértice (bi+1) no rota
	    var dx=pt.x, dy=pt.y-pl.rest, c=Math.cos(a*DEG), sn=Math.sin(a*DEG);
	    return {x:dx*c-dy*sn, y:(dx*sn+dy*c)+pl.rest - foldFrac*pen};   // el vértice baja la penetración a la V
	  });
	  var segs=[]; for(var k=0;k<p.flanges.length;k++) segs.push({a:P[k],b:P[k+1],tip:(k===bi||k===bi+1)});
	  return {P:P,segs:segs,pen:pen};
	}
	function drawMachine(step){
	  if(state.useW&&state.plan.wPlan) return;   // técnica W: sin vista de máquina
	  var p=state.plan, st=p.steps[step];
	  var gNow=machineGeom(step,0), gPost=machineGeom(step,1);
	  var tipRest=p.s+10;                 // punzón en reposo (punto muerto superior)
	  var tipForm=-gPost.pen;             // punzón apoyado contra la chapa (punto muerto inferior de este pliegue)
	  var tipDraw=state.punchDown?tipForm:tipRest;
	  var PSd=punchSegs(); var punch=[]; for(var u=0;u<PSd.length;u++){ var s0=PSd[u]; if(Math.min(s0[0][1],s0[1][1])<=95) punch.push([[s0[0][0],s0[0][1]+tipDraw],[s0[1][0],s0[1][1]+tipDraw]]); }
	  // punzón formado (para marcar dónde chocaría, siempre a fondo, independiente del toggle de dibujo)
	  var punchF=[]; for(var u2=0;u2<PSd.length;u2++){ var s1=PSd[u2]; if(Math.min(s1[0][1],s1[1][1])<=95) punchF.push([{x:s1[0][0],y:s1[0][1]+tipForm},{x:s1[1][0],y:s1[1][1]+tipForm}]); }
	  var XS=[-30,30],YS=[-15,tipRest+50];
	  if(state.zoomDie){   // vista centrada en el vértice del pliegue activo: las colas largas salen de cuadro
	    var bvi=st.bendIndex+1, vx=gNow.P[bvi].x, vy=gNow.P[bvi].y;
	    XS=[vx-MACHINE_CLIP, vx+MACHINE_CLIP]; YS=[vy-20, vy+tipRest+40];
	  }
	  else { var allP=gNow.P.concat(gPost.P); for(var i=0;i<allP.length;i++){ XS.push(allP[i].x); YS.push(allP[i].y); } }
	  var minx=Math.min.apply(null,XS)-6,maxx=Math.max.apply(null,XS)+6,miny=Math.min.apply(null,YS)-6,maxy=Math.max.apply(null,YS)+6;
	  var W=460,H=300,pad=10; var sc=Math.min((W-2*pad)/(maxx-minx),(H-2*pad)/(maxy-miny));
	  var ox=(W-(maxx-minx)*sc)/2, oy=(H-(maxy-miny)*sc)/2;
	  function TX(x){return ox+(x-minx)*sc;} function TY(y){return H-(oy+(y-miny)*sc);}
	  function Ln(a,b,col,w,dash){ var ax=a.x!==undefined?a.x:a[0],ay=a.y!==undefined?a.y:a[1],bx=b.x!==undefined?b.x:b[0],by=b.y!==undefined?b.y:b[1]; return '<line x1="'+TX(ax).toFixed(1)+'" y1="'+TY(ay).toFixed(1)+'" x2="'+TX(bx).toFixed(1)+'" y2="'+TY(by).toFixed(1)+'" stroke="'+col+'" stroke-width="'+w+'" stroke-linecap="round"'+(dash?' stroke-dasharray="'+dash+'"':'')+'/>'; }
	  var svg='';
	  var rr=dieRot(); var DS=(rr&&rr.segs)?rr.segs:null;
	  if(DS){ for(var dz=0;dz<DS.length;dz++){ var dd=DS[dz]; if(Math.max(dd[0][1],dd[1][1])>-55) svg+=Ln({x:dd[0][0],y:dd[0][1]},{x:dd[1][0],y:dd[1][1]},'#7e9bc0',1.6,''); } }
	  else { var dpath='M'; for(var k=0;k<DIE.length;k++){ dpath+=' '+TX(DIE[k][0]).toFixed(1)+' '+TY(DIE[k][1]).toFixed(1)+(k===0?' L':''); } dpath+=' Z'; svg+='<path d="'+dpath+'" fill="#e3edf8" stroke="#8aa0bd" stroke-width="1.4"/>'; }
	  for(var q=0;q<punch.length;q++) svg+=Ln({x:punch[q][0][0],y:punch[q][0][1]},{x:punch[q][1][0],y:punch[q][1][1]},'#9ab0cd',1.4,'');
	  svg+='<line x1="'+TX(0).toFixed(1)+'" y1="'+TY(maxy).toFixed(1)+'" x2="'+TX(0).toFixed(1)+'" y2="'+TY(miny).toFixed(1)+'" stroke="#6e8aae" stroke-width="1" stroke-dasharray="3 4"/>';
	  var sw=(2+p.s*0.7).toFixed(1);
	  // AHORA (gris, antes del pliegue)
	  for(var c=0;c<gNow.segs.length;c++){ svg+=Ln(gNow.segs[c].a,gNow.segs[c].b,'#5b7a9e',sw,'1 6'); }
	  // DESPUÉS (azul; rojo donde chocaría)
	  for(var d3=0;d3<gPost.segs.length;d3++){ var sg=gPost.segs[d3]; var col='#2f8ef7';
	    if(!sg.tip){ for(var b2=0;b2<punchF.length;b2++){ if(segInt(sg.a,sg.b,punchF[b2][0],punchF[b2][1])){ col='#f06c92'; break; } } }
	    svg+=Ln(sg.a,sg.b,col,sw,''); }
	  // tope: en el NODO DE APOYO ELEGIDO para este paso (no el automático)
	  var gnode=(st.gaugeNode!=null && st.gaugeNode<gNow.P.length)?gNow.P[st.gaugeNode]:null;
	  if(!gnode){ gnode=gNow.P[0]; for(var m3=1;m3<gNow.P.length;m3++) if(gNow.P[m3].x>gnode.x) gnode=gNow.P[m3]; }
	  var ty=p.s;   // el tope está a la altura de la mesa
	  svg+=Ln({x:gnode.x,y:ty+16},{x:gnode.x,y:ty-6},'#19b877',3,'');
	  svg+='<text x="'+TX(gnode.x).toFixed(1)+'" y="'+TY(ty-9).toFixed(1)+'" fill="#19b877" font-size="13" font-weight="700" text-anchor="middle">tope '+(st.gaugeNode!=null?nodeLetter(st.gaugeNode):'')+'</text>';
	  document.getElementById('pp-machine').innerHTML=svg;
	}

	/* ===== OPERACIÓN ===== */
	function showStepW(){
	  var p=state.plan, ws=p.wPlan[state.step], n=p.wPlan.length;
	  document.getElementById('pp-stepTitle').textContent='Paso '+(state.step+1)+' de '+n+' — '+(p.wTipo==='escalon'?'técnica de escalón':'técnica W');
	  document.getElementById('pp-angleLine').innerHTML='<b>'+ws.label+'</b>';
	  document.getElementById('pp-valX').textContent=ws.X;
	  document.getElementById('pp-uX').textContent='mm';
	  document.getElementById('pp-valY').textContent=ws.Y;
	  var dots=''; for(var i=0;i<n;i++) dots+='<span class="dot '+(i<state.step?'done':(i===state.step?'cur':''))+'"></span>';
	  document.getElementById('pp-dots').innerHTML=dots;
	  document.getElementById('pp-stepWarn').innerHTML='<div class="warn" style="background:#fff8ec;border-color:#e89c1a;color:#a56200;">'+ws.hint+'</div>';
	  document.getElementById('pp-stepHelp').textContent='Punzón: '+ws.punch+' · Matriz: '+ws.die+'. Cargá X='+ws.X+(ws.Y!=='—'?' e Y='+ws.Y:'')+' en el E21.';
	  document.getElementById('pp-next').textContent=(state.step===n-1)?'Terminar ✓':'Siguiente ▸';
	  document.getElementById('pp-machine').innerHTML='<text x="230" y="150" text-anchor="middle" fill="#8aa0bd" font-size="14">Técnica W — seguí la indicación del paso</text>';
	}
	function showStep(){
	  if(state.useW&&state.plan.wPlan){ showStepW(); return; }
	  var p=state.plan, st=p.steps[state.step], n=p.steps.length;
	  document.getElementById('pp-stepTitle').textContent='Paso '+(state.step+1)+' de '+n+' — pliegue b'+(st.bendIndex+1);
	  var _corr=(state.angCorr&&state.angCorr[st.alpha])||0;
	  document.getElementById('pp-angleLine').innerHTML='Ángulo: <b>'+st.alpha+'°'+(p.dirs[st.bendIndex]<0?' ↓':' ↑')+'</b>  (formar a '+(st.alpha-p.sb-_corr).toFixed(1)+'° por retorno'+(_corr?' · corr. empírica '+(-_corr>0?'+':'')+(-_corr).toFixed(1)+'°':'')+')';
	  document.getElementById('pp-valX').textContent=st.X.toFixed(1);
	  var _dx=st.X-st.Xraw;
	  document.getElementById('pp-uX').textContent='mm'+(Math.abs(_dx)>=0.005?' · corr. '+(_dx>0?'+':'')+_dx.toFixed(2):'');
	  document.getElementById('pp-valY').textContent=st.Y.toFixed(2);
	  var dots=''; for(var i=0;i<n;i++){ var cls=i<state.step?'done':(i===state.step?'cur':''); if(!p.steps[i].ok) cls='bad'; dots+='<span class="dot '+cls+'"></span>'; }
	  document.getElementById('pp-dots').innerHTML=dots;
	  var sw=document.getElementById('pp-stepWarn'); sw.innerHTML='';
	  if(!st.ok) sw.innerHTML+='<div class="warn bad">⚠︎ Choque en este paso: '+st.warns[0]+'. Revisá útil o estrategia.</div>';
	  for(var w=(st.ok?0:1);w<st.warns.length;w++) sw.innerHTML+='<div class="warn">⚠︎ '+st.warns[w]+'</div>';
	  if(st.my&&state.step>0) sw.innerHTML+='<div class="warn" style="background:#eef4ff;border-color:#8aabdf;color:#1d4ed8;">ℹ️ En este paso la pieza va <b>dada vuelta</b> (cara opuesta arriba): los pliegues ya hechos se ven apuntando para abajo en el dibujo. El perfil final sale igual al que dibujaste.</div>';
	  var man=(st.mx?'girá la pieza (otro extremo al tope)':'')+((st.mx&&st.my)?' y ':'')+(st.my?'dala vuelta (cara opuesta arriba)':'');
	  document.getElementById('pp-stepHelp').textContent='Posicioná la pieza así'+(man?'; '+man:'')+'. Cargá X='+st.X.toFixed(1)+' e Y='+st.Y.toFixed(2)+' en el E21.';
	  document.getElementById('pp-next').textContent=(state.step===n-1)?'Terminar ✓':'Siguiente ▸';
	  drawMachine(state.step);
	}

	/* ===== NAV ===== */
	function show(id){ var s=document.querySelectorAll('#pp-root .screen'); for(var i=0;i<s.length;i++) s[i].classList.remove('active'); document.getElementById(id).classList.add('active'); window.scrollTo(0,0); }
	document.getElementById('pp-calc').addEventListener('click',function(){
	  var n=0,bad=false; for(var i=0;i<state.segs.length;i++){ if(state.segs[i].len!=null&&!isNaN(state.segs[i].len)) n++; }
	  for(var j=0;j<state.segs.length-1;j++){ if(state.segs[j].ang==null||isNaN(state.segs[j].ang)) state.segs[j].ang=90; }
	  if(n<2){ document.getElementById('pp-setupMsg').innerHTML='<div class="warn">Cargá al menos 2 medidas.</div>'; return; }
	  // descartar alas vacías finales
	  while(state.segs.length>2 && (state.segs[state.segs.length-1].len==null||isNaN(state.segs[state.segs.length-1].len))){ state.segs.pop(); state.segs[state.segs.length-1].ang=null; }
	  document.getElementById('pp-setupMsg').innerHTML=''; state.manual=false; state.manSeq=null; state.useW=false; state.keepOrder=null; state.plan=buildPlan(); state.step=0; showResult();
	});
	/* "Volver a la secuencia": recalcular con las medidas nuevas SIN perder el orden elegido
	   (mantiene modo manual y técnica aceptada). Si cambió la cantidad de pliegues, cae al
	   cálculo completo. */
	document.getElementById('pp-btnBackSeq').addEventListener('click',function(){
	  var n=0; for(var i=0;i<state.segs.length;i++){ if(state.segs[i].len!=null&&!isNaN(state.segs[i].len)) n++; }
	  for(var j=0;j<state.segs.length-1;j++){ if(state.segs[j].ang==null||isNaN(state.segs[j].ang)) state.segs[j].ang=90; }
	  if(n<2){ document.getElementById('pp-setupMsg').innerHTML='<div class="warn">Cargá al menos 2 medidas.</div>'; return; }
	  while(state.segs.length>2 && (state.segs[state.segs.length-1].len==null||isNaN(state.segs[state.segs.length-1].len))){ state.segs.pop(); state.segs[state.segs.length-1].ang=null; }
	  var nb=state.segs.length-1;
	  if(!state.plan){ state.manual=false; state.manSeq=null; state.useW=false; state.keepOrder=null; }
	  else if(state.manual){ if(!state.manSeq||state.manSeq.length!==nb){ state.manual=false; state.manSeq=null; } }
	  else {
	    // congelar el SETUP de cada paso: pliegue + nodo de tope (formato de simulateManual)
	    var ord=[]; for(var k=0;k<state.plan.steps.length;k++){ var st=state.plan.steps[k];
	      if(st.bendIndex!=null && st.gaugeNode!=null) ord.push({bend:st.bendIndex, node:st.gaugeNode}); }
	    state.keepOrder=(ord.length===nb)?ord:null;
	  }
	  document.getElementById('pp-setupMsg').innerHTML='';
	  state.plan=buildPlan(); state.step=0; showResult();
	});
	document.getElementById('pp-btnCil').addEventListener('click',function(){
	  var panel=document.getElementById('pp-cilPanel'), vis=panel.style.display!=='none';
	  panel.style.display=vis?'none':'block';
	  this.textContent=vis?'⌒ Cilindrado (bump bending)':'⌒ Cilindrado ✕ cerrar';
	});
	document.getElementById('pp-calcCil').addEventListener('click',showCilindrado);
	document.getElementById('pp-btnManual').addEventListener('click',toggleManual);
	document.getElementById('pp-back1').addEventListener('click',function(){ document.getElementById('pp-btnBackSeq').style.display=state.plan?'':'none'; show('pp-setup'); });
	document.getElementById('pp-goRun').addEventListener('click',function(){ state.step=0; state.zoomDie=true; state.punchDown=false; document.getElementById('pp-btnZoom').classList.add('on'); document.getElementById('pp-btnPunchDown').classList.remove('on'); show('pp-run'); showStep(); });
	document.getElementById('pp-exitRun').addEventListener('click',function(){ show('pp-result'); });
	document.getElementById('pp-next').addEventListener('click',function(){ var len=(state.useW&&state.plan.wPlan)?state.plan.wPlan.length:state.plan.steps.length; if(state.step<len-1){ state.step++; showStep(); } else { show('pp-result'); } });
	document.getElementById('pp-prev').addEventListener('click',function(){ if(state.step>0){ state.step--; showStep(); } });
	document.getElementById('pp-btnZoom').addEventListener('click',function(){ state.zoomDie=!state.zoomDie; this.classList.toggle('on',state.zoomDie); drawMachine(state.step); });
	document.getElementById('pp-btnPunchDown').addEventListener('click',function(){ state.punchDown=!state.punchDown; this.classList.toggle('on',state.punchDown); drawMachine(state.step); });
	/* corrección de ángulo empírica (flujo Cybelec): plegar prueba → medir → cargar → la app corrige la Y sola */
	document.getElementById('pp-btnAngCorr').addEventListener('click',function(){
	  var p=state.plan, st=p.steps[state.step]; if(!st||st.bendIndex==null) return;
	  var tgt=st.alpha, cur=(state.angCorr&&state.angCorr[tgt])||0;
	  var msg='¿Qué ángulo midió la pieza? (objetivo '+tgt+'°)\nLa corrección se aplica a TODOS los pliegues de '+tgt+'° y se puede repetir hasta clavar el ángulo.'+(cur?'\nCorrección acumulada: '+(-cur>0?'+':'')+(-cur).toFixed(1)+'° (escribí R para borrarla)':'');
	  var r=prompt(msg,String(tgt));
	  if(r===null) return;
	  r=r.replace(/\s+/g,'');
	  if(/^r$/i.test(r)){ if(state.angCorr) delete state.angCorr[tgt]; }
	  else {
	    var m=parseFloat(r.replace(',','.'));
	    if(isNaN(m)||m<=0||m>=180){ alert('Cargá un ángulo entre 0 y 180 (ej. 92 o 91,5).'); return; }
	    if(!state.angCorr) state.angCorr={};
	    state.angCorr[tgt]=cur+(m-tgt);
	    if(Math.abs(state.angCorr[tgt])<0.05) delete state.angCorr[tgt];   // quedó clavado: sin corrección
	  }
	  state.plan=buildPlan(); showStep();
	});
	/* corrección X fina por pliegue: medir el ala real → ajustar el tope de ese pliegue */
	document.getElementById('pp-btnXCorr').addEventListener('click',function(){
	  var p=state.plan, st=p.steps[state.step]; if(!st||st.bendIndex==null) return;
	  var bi=st.bendIndex, cur=(state.xCorr&&state.xCorr[bi])||0;
	  var msg='¿Cuánto midió el ala contra el tope? (debía dar '+st.Xraw.toFixed(1)+' mm)\nLa corrección es solo para el pliegue b'+(bi+1)+'.'+(cur?'\nCorrección acumulada: '+(cur>0?'+':'')+cur.toFixed(2)+' mm (escribí R para borrarla)':'');
	  var r=prompt(msg,st.Xraw.toFixed(1));
	  if(r===null) return;
	  r=r.replace(/\s+/g,'');
	  if(/^r$/i.test(r)){ if(state.xCorr) delete state.xCorr[bi]; }
	  else {
	    var m=parseFloat(r.replace(',','.'));
	    if(isNaN(m)||m<=0){ alert('Cargá la medida en mm (ej. 20.5 o 20,5).'); return; }
	    if(!state.xCorr) state.xCorr={};
	    state.xCorr[bi]=cur+(st.Xraw-m);
	    if(Math.abs(state.xCorr[bi])<0.02) delete state.xCorr[bi];   // quedó clavada
	  }
	  state.plan=buildPlan(); showStep();
	});

	/* calibración */
	function openCal(){ var c=getCal(); document.getElementById('pp-calY90').value=c.y90; document.getElementById('pp-calSign').value=String(c.sign); document.getElementById('pp-calXg').value=c.xg||0; document.getElementById('pp-calModal').style.display='block'; }
	document.getElementById('pp-btnCal').addEventListener('click',openCal);
	document.getElementById('pp-calClose').addEventListener('click',function(){ setCal({y90:parseFloat(document.getElementById('pp-calY90').value)||0,sign:parseInt(document.getElementById('pp-calSign').value,10),xg:parseFloat(document.getElementById('pp-calXg').value)||0}); document.getElementById('pp-calModal').style.display='none'; previewSetup(); });
	document.getElementById('pp-calModal').style.display='none';

	/* recalcular desarrollo en vivo cuando cambian útiles */
	['s','V','ri'].forEach(function(id){ document.getElementById('pp-'+id).addEventListener('change',previewSetup); });

	/* ===== SELECTOR DE ÚTILES ===== */
	function orientPunch(p){
	  // el lado MÁS ALTO del punzón va hacia afuera (derecha, +x)
	  var maxy=-1e9, atx=0;
	  for(var i=0;i<p.segs.length;i++){ for(var e=0;e<2;e++){ if(p.segs[i][e][1]>maxy){ maxy=p.segs[i][e][1]; atx=p.segs[i][e][0]; } } }
	  if(atx>=0) return p;
	  var segs=p.segs.map(function(s){ return [[-s[0][0],s[0][1]],[-s[1][0],s[1][1]]]; });
	  return {id:p.id,name:p.name,minA:p.minA,ri:p.ri,segs:segs};
	}
	function setPunch(i){ curPunch=TOOLS.punzones[i]||null; if(curPunch&&curPunch.ri) document.getElementById('pp-ri').value=curPunch.ri; updateToolBtns(); previewSetup(); }   /* sin espejar: tal cual el CAD */
	function setDie(i){ curDie=TOOLS.matrices[i]; curRot=0; var r=dieRot(); if(r) document.getElementById('pp-V').value=r.V; updateToolBtns(); previewSetup(); }
	function rotateDie(){ if(!curDie||!curDie.rotations) return; curRot=(curRot+1)%curDie.rotations.length; var r=dieRot(); if(r) document.getElementById('pp-V').value=r.V; updateToolBtns(); previewSetup(); }
	function segsThumb(segs,W,H,color){
	  var minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9,i,e;
	  for(i=0;i<segs.length;i++){ for(e=0;e<2;e++){ var x=segs[i][e][0],y=segs[i][e][1]; if(x<minx)minx=x; if(y<miny)miny=y; if(x>maxx)maxx=x; if(y>maxy)maxy=y; } }
	  var pad=8, sc=Math.min((W-2*pad)/Math.max(1,maxx-minx),(H-2*pad)/Math.max(1,maxy-miny));
	  var ox=(W-(maxx-minx)*sc)/2, oy=(H-(maxy-miny)*sc)/2;
	  function TX(x){return ox+(x-minx)*sc;} function TY(y){return H-(oy+(y-miny)*sc);}
	  var svg='<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:'+H+'px;background:#fff;border:none;">';
	  for(i=0;i<segs.length;i++){ var d=segs[i]; svg+='<line x1="'+TX(d[0][0]).toFixed(1)+'" y1="'+TY(d[0][1]).toFixed(1)+'" x2="'+TX(d[1][0]).toFixed(1)+'" y2="'+TY(d[1][1]).toFixed(1)+'" stroke="'+(color||'#3a5681')+'" stroke-width="2" stroke-linecap="round"/>'; }
	  return svg+'</svg>';
	}
	function updateToolBtns(){
	  if(curPunch) document.getElementById('pp-btnPunchSel').innerHTML=segsThumb(curPunch.segs,120,54,'#3a5681')+'<div class="toolname">'+curPunch.name+'</div>';
	  var r=dieRot();
	  if(r) document.getElementById('pp-btnDieSel').innerHTML=segsThumb(r.segs,120,54,'#0a8294')+'<div class="toolname">'+curDie.name+(curDie.multi?' · V'+r.V:'')+'</div>';
	  var rr=document.getElementById('pp-rotRow'); rr.style.display=(curDie&&curDie.multi)?'block':'none';
	  if(curDie&&curDie.multi&&r) document.getElementById('pp-btnRotate').textContent='Girar dado 90° ↻  (cara '+(curRot+1)+'/'+curDie.rotations.length+' · V'+r.V+')';
	}
	function openGallery(cat){
	  var arr=(cat==='punch')?TOOLS.punzones:TOOLS.matrices, col=(cat==='punch')?'#3a5681':'#0a8294';
	  document.getElementById('pp-galTitle').textContent=(cat==='punch')?'Elegí el punzón':'Elegí la matriz';
	  var h='<div style="display:flex;flex-wrap:wrap;margin:0 -6px;">', i;
	  for(i=0;i<arr.length;i++){ var t=arr[i]; var sg=(cat==='punch')?t.segs:t.rotations[0].segs;
	    var extra=(cat==='punch')?('hasta '+t.minA+'°'):(t.multi?'4 caras (girable)':'V'+t.rotations[0].V+' · '+t.rotations[0].angle+'°');
	    h+='<div class="galcard" data-cat="'+cat+'" data-i="'+i+'">'+segsThumb(sg,150,86,col)+'<div class="toolname">'+t.name+'</div><div class="galsub">'+extra+'</div></div>';
	  }
	  document.getElementById('pp-galGrid').innerHTML=h+'</div>';
	  var cards=document.getElementById('pp-galGrid').querySelectorAll('.galcard');
	  for(i=0;i<cards.length;i++){ cards[i].addEventListener('click',function(e){ var el=e.currentTarget, ix=+el.getAttribute('data-i'); if(el.getAttribute('data-cat')==='punch') setPunch(ix); else setDie(ix); document.getElementById('pp-galleryModal').style.display='none'; }); }
	  document.getElementById('pp-galleryModal').style.display='block';
	}
	document.getElementById('pp-btnPunchSel').addEventListener('click',function(){ openGallery('punch'); });
	document.getElementById('pp-btnDieSel').addEventListener('click',function(){ openGallery('die'); });
	document.getElementById('pp-btnRotate').addEventListener('click',rotateDie);
	document.getElementById('pp-galClose').addEventListener('click',function(){ document.getElementById('pp-galleryModal').style.display='none'; });
	/* ===== GALERÍA DE PIEZAS (localStorage) ===== */
	function getGaleria(){ try{ var r=localStorage.getItem('plegado_galeria'); if(r) return JSON.parse(r); }catch(e){} return []; }
	function setGaleria(a){ try{ localStorage.setItem('plegado_galeria',JSON.stringify(a)); return true; }catch(e){ alert('No se pudo guardar (almacenamiento lleno).'); return false; } }
	function toolIndexById(arr,id){ for(var i=0;i<arr.length;i++) if(arr[i].id===id) return i; return -1; }
	function escapeHtml(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
	function segsToFAD(segs){
	  var fl=[],an=[],dr=[],i;
	  for(i=0;i<segs.length;i++) fl.push(segs[i].len||0);
	  for(i=0;i<segs.length-1;i++){ var a=(segs[i].ang==null?90:segs[i].ang); an.push(Math.abs(a)); dr.push(a<0?-1:1); }
	  return {fl:fl,an:an,dr:dr};
	}
	function partThumb(segs,W,H){
	  var t=segsToFAD(segs), g=partPoints(t.fl,t.an,t.dr);
	  var bx0=1e9,by0=1e9,bx1=-1e9,by1=-1e9,q;
	  for(q=0;q<g.pts.length;q++){ var p=g.pts[q]; if(p.x<bx0)bx0=p.x; if(p.y<by0)by0=p.y; if(p.x>bx1)bx1=p.x; if(p.y>by1)by1=p.y; }
	  var rot90=((by1-by0)>(bx1-bx0)*1.05);
	  function tr(x,y){ return rot90?{x:y,y:-x}:{x:x,y:y}; }
	  var S=g.segs.map(function(s){ var a=tr(s.x1,s.y1),b=tr(s.x2,s.y2); return [a,b]; });
	  var minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9,i,e;
	  for(i=0;i<S.length;i++){ for(e=0;e<2;e++){ var x=S[i][e].x,y=S[i][e].y; if(x<minx)minx=x; if(y<miny)miny=y; if(x>maxx)maxx=x; if(y>maxy)maxy=y; } }
	  var pad=12, sc=Math.min((W-2*pad)/Math.max(1,maxx-minx),(H-2*pad)/Math.max(1,maxy-miny));
	  var ox=(W-(maxx-minx)*sc)/2, oy=(H-(maxy-miny)*sc)/2;
	  function TX(x){return ox+(x-minx)*sc;} function TY(y){return H-(oy+(y-miny)*sc);}
	  var svg='<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:'+H+'px;background:#fff;border:none;">';
	  for(i=0;i<S.length;i++){ svg+='<line x1="'+TX(S[i][0].x).toFixed(1)+'" y1="'+TY(S[i][0].y).toFixed(1)+'" x2="'+TX(S[i][1].x).toFixed(1)+'" y2="'+TY(S[i][1].y).toFixed(1)+'" stroke="#5b7a9e" stroke-width="3" stroke-linecap="round"/>'; }
	  return svg+'</svg>';
	}
	function partDefaultName(segs){ var f=[],i; for(i=0;i<segs.length;i++) if(segs[i].len!=null&&!isNaN(segs[i].len)) f.push(segs[i].len); return 'Pieza '+f.join('-'); }
	function savePart(){
	  var segs=[],i; for(i=0;i<state.segs.length;i++){ if(state.segs[i].len==null||isNaN(state.segs[i].len)) continue; segs.push({len:state.segs[i].len,ang:(i<state.segs.length-1?state.segs[i].ang:null)}); }
	  if(segs.length<2){ alert('Cargá al menos 2 medidas antes de guardar.'); return; }
	  segs[segs.length-1].ang=null;
	  var def=partDefaultName(segs), name=prompt('Nombre de la pieza:',def); if(name===null) return; if(!name) name=def;
	  var val=function(id){ return document.getElementById('pp-'+id).value; };
	  var rec={ name:name, segs:segs, s:val('s'), V:val('V'), ri:val('ri'), sb:val('sb'), Rm:val('Rm'), L:val('L'),
	            punchId:(curPunch?curPunch.id:null), dieId:(curDie?curDie.id:null), rot:curRot,
	            angCorr:(state.angCorr&&Object.keys(state.angCorr).length?state.angCorr:null),
	            xCorr:(state.xCorr&&Object.keys(state.xCorr).length?state.xCorr:null), ts:(new Date()).getTime() };
	  var g=getGaleria(); g.unshift(rec);
	  if(setGaleria(g)){ var m=document.getElementById('pp-setupMsg'); m.innerHTML='<div class="warn" style="background:#e6f9f4;border-color:#a3e6dc;color:#0a6b57;">✓ Guardada «'+escapeHtml(name)+'» en la galería.</div>'; setTimeout(function(){ m.innerHTML=''; },2500); }
	}
	function loadPart(idx){
	  var g=getGaleria(), p=g[idx]; if(!p) return;
	  state.segs=[]; var i; for(i=0;i<p.segs.length;i++) state.segs.push({len:p.segs[i].len,ang:p.segs[i].ang});
	  if(state.segs.length<2) state.segs=[{len:50,ang:90},{len:50,ang:null}];
	  state.segs[state.segs.length-1].ang=null;
	  if(p.punchId!=null){ var pi=toolIndexById(TOOLS.punzones,p.punchId); if(pi>=0) setPunch(pi); }
	  if(p.dieId!=null){ var di=toolIndexById(TOOLS.matrices,p.dieId); if(di>=0){ setDie(di); if(p.rot&&curDie&&curDie.rotations){ curRot=p.rot%curDie.rotations.length; var r=dieRot(); if(r) document.getElementById('pp-V').value=r.V; updateToolBtns(); } } }
	  ['s','V','ri','sb','Rm','L'].forEach(function(k){ if(p[k]!=null&&p[k]!=='') document.getElementById('pp-'+k).value=p[k]; });
	  state.angCorr=p.angCorr||{}; state.xCorr=p.xCorr||{};   // la pieza guardada trae sus correcciones empíricas ya afinadas
	  state.plan=null; state.manual=false; state.manSeq=null; state.useW=false; state.keepOrder=null; state.step=0;
	  document.getElementById('pp-btnBackSeq').style.display='none';
	  renderSegs(); previewSetup();
	  document.getElementById('pp-partsModal').style.display='none'; show('pp-setup');
	}
	function deletePart(idx){ var g=getGaleria(); g.splice(idx,1); setGaleria(g); openParts(); }
	function openParts(){
	  var g=getGaleria(), h, i;
	  if(!g.length){ h='<p class="muted" style="text-align:center;margin-top:34px;">Todavía no guardaste ninguna pieza.<br>Dibujá una y tocá <b>💾 Guardar</b>.</p>'; }
	  else {
	    h='<div style="display:flex;flex-wrap:wrap;margin:0 -6px;">';
	    for(i=0;i<g.length;i++){ var p=g[i], n=0,j; for(j=0;j<p.segs.length;j++) if(p.segs[j].len!=null) n++;
	      h+='<div class="galcard partcard" data-i="'+i+'">'
	        +'<button class="ghost delpart" data-del="'+i+'" type="button">✕</button>'
	        +partThumb(p.segs,150,86)
	        +'<div class="toolname">'+escapeHtml(p.name)+'</div>'
	        +'<div class="galsub">'+n+' alas · V'+escapeHtml(p.V||'?')+' · '+escapeHtml(p.s||'?')+'mm</div></div>';
	    }
	    h+='</div>';
	  }
	  document.getElementById('pp-partsGrid').innerHTML=h;
	  var cards=document.getElementById('pp-partsGrid').querySelectorAll('.partcard');
	  for(i=0;i<cards.length;i++){ cards[i].addEventListener('click',function(e){ loadPart(+e.currentTarget.getAttribute('data-i')); }); }
	  var dels=document.getElementById('pp-partsGrid').querySelectorAll('.delpart');
	  for(i=0;i<dels.length;i++){ dels[i].addEventListener('click',function(e){ e.stopPropagation(); var ix=+e.currentTarget.getAttribute('data-del'); if(confirm('¿Borrar esta pieza de la galería?')) deletePart(ix); }); }
	  document.getElementById('pp-partsModal').style.display='block';
	}
	document.getElementById('pp-btnSavePart').addEventListener('click',savePart);
	document.getElementById('pp-btnGallery').addEventListener('click',openParts);
	document.getElementById('pp-partsClose').addEventListener('click',function(){ document.getElementById('pp-partsModal').style.display='none'; });
	document.getElementById('pp-partsModal').style.display='none';

	setPunch(2); setDie(1);   /* Recto por defecto */
	document.getElementById('pp-btnDxf').addEventListener('click',exportDXF);
	renderSegs(); previewSetup();
	/* ===== PEDIDO: PRECIOS Y MATERIALES (Frappe) ===== */
	var _precios = { precio_por_plegado: 0, precio_segundo_laser: 0 };
	var _matEspesores = {};   // {material: [rows de SI Material Corte, orden por espesor]}

	function _fetchPrices(){
	  frappe.call({
	    method: 'sistema_industrial.api.materiales.get_precios',
	    callback: function(r){ if(r.message){ _precios = r.message; _updatePresup(); } }
	  });
	}
	function _fetchMaterials(){
	  frappe.call({
	    method: 'sistema_industrial.api.materiales.get_all',
	    callback: function(r){
	      var rows = ((r.message || {}).rows || []).filter(function(m){ return m.activo; });
	      _matEspesores = {};
	      rows.forEach(function(m){
	        if(!_matEspesores[m.material]) _matEspesores[m.material] = [];
	        _matEspesores[m.material].push(m);
	      });
	      Object.keys(_matEspesores).forEach(function(n){
	        _matEspesores[n].sort(function(a, b){ return a.espesor_mm - b.espesor_mm; });
	      });
	      var sel = document.getElementById('pp-ped-material');
	      sel.innerHTML = '<option value="">— elegir —</option>';
	      Object.keys(_matEspesores).sort().forEach(function(n){
	        var o = document.createElement('option'); o.value = n; o.textContent = n; sel.appendChild(o);
	      });
	    },
	    error: function(){
	      document.getElementById('pp-ped-material').innerHTML = '<option value="">Error al cargar materiales</option>';
	    }
	  });
	}

	document.getElementById('pp-ped-material').addEventListener('change', function(){
	  var mat = this.value;
	  var esSel = document.getElementById('pp-ped-espesor');
	  esSel.innerHTML = '<option value="">—</option>';
	  esSel.disabled = true;
	  if(!mat || !_matEspesores[mat]) return;
	  _matEspesores[mat].forEach(function(m){
	    var o = document.createElement('option'); o.value = m.espesor_mm; o.textContent = m.espesor_mm + ' mm'; esSel.appendChild(o);
	  });
	  esSel.disabled = false;
	  if(_matEspesores[mat].length === 1) esSel.value = String(_matEspesores[mat][0].espesor_mm);
	  _updatePresup();
	});

	document.getElementById('pp-ped-espesor').addEventListener('change', function(){
	  var v = parseFloat(this.value);
	  if(v > 0) document.getElementById('pp-s').value = v;
	  _updatePresup();
	});

	document.getElementById('pp-ped-cant').addEventListener('input', _updatePresup);

	// Row de SI Material Corte según material+espesor elegidos
	function _selectedMatRow(){
	  var mat = document.getElementById('pp-ped-material').value;
	  var esp = parseFloat(document.getElementById('pp-ped-espesor').value);
	  if(!mat || isNaN(esp) || !_matEspesores[mat]) return null;
	  for(var i = 0; i < _matEspesores[mat].length; i++){
	    if(Math.abs(_matEspesores[mat][i].espesor_mm - esp) < 0.001) return _matEspesores[mat][i];
	  }
	  return null;
	}

	function _fmt(n){ return isNaN(n) || !isFinite(n) ? '—' : '$ ' + Math.round(n).toLocaleString('es-AR'); }

	function _updatePresup(){
	  if(!state.plan) return;
	  var p = state.plan;
	  var devel = p.devel, nbends = p.nbends;
	  var L = parseFloat(document.getElementById('pp-L').value) || 0;
	  var s = parseFloat(document.getElementById('pp-s').value) || 0;
	  var cant = parseInt(document.getElementById('pp-ped-cant').value) || 1;
	  var mrow = _selectedMatRow();
	  var densidadM2 = mrow ? (parseFloat(mrow.densidad_kg_m2) || 0) : 0;   // kg/m² (ya incluye el espesor)
	  var precioKg = mrow ? (parseFloat(mrow.precio_por_kg) || 0) : 0;
	  var precioDoblez = _precios.precio_por_plegado || 0;

	  document.getElementById('pp-devel').textContent = devel ? devel.toFixed(1) + ' mm' : '—';
	  document.getElementById('pp-nbends').textContent = nbends;
	  document.getElementById('pp-cant').textContent = cant;

	  var pesoUnit = (densidadM2 && L && devel) ? (devel / 1000) * (L / 1000) * densidadM2 : 0;
	  var costoMatUnit = pesoUnit * precioKg;
	  var costoPlegUnit = nbends * precioDoblez;
	  var totalUnit = costoMatUnit + costoPlegUnit;
	  var totalTotal = totalUnit * cant;

	  var matLabel = mrow ? document.getElementById('pp-ped-material').value : '—';
	  document.getElementById('pp-mat-desc').textContent = matLabel + (s ? ' ' + s + 'mm' : '') + (pesoUnit ? ' · ' + pesoUnit.toFixed(3) + ' kg/ud' : '');
	  document.getElementById('pp-mat-cost').textContent = precioKg ? _fmt(costoMatUnit) + ' / ud' : '— (sin precio)';
	  document.getElementById('pp-pleg-desc').textContent = precioDoblez ? ('× $' + Math.round(precioDoblez).toLocaleString('es-AR') + '/doblez') : '— (sin precio)';
	  document.getElementById('pp-pleg-cost').textContent = precioDoblez ? _fmt(costoPlegUnit) + ' / ud' : '—';
	  document.getElementById('pp-total').textContent = (totalTotal > 0) ? _fmt(totalTotal) : '—';

	  state._presup = { devel_mm: devel, n_pliegues: nbends, L_mm: L, s_mm: s,
	    material_corte: mrow ? mrow.name : '', densidad_kg_m2: densidadM2, peso_unit_kg: pesoUnit,
	    precio_kg: precioKg, precio_doblez: precioDoblez, costo_mat_unit: costoMatUnit,
	    costo_pleg_unit: costoPlegUnit, total_unit: totalUnit, total: totalTotal, cantidad: cant };
	}

	// Hook en showResult para refrescar el presupuesto
	var _origShowResult = showResult;
	showResult = function(){
	  _origShowResult.apply(this, arguments);
	  _updatePresup();
	};

	/* ===== GUARDAR PEDIDO ===== */
	document.getElementById('pp-btnSavePedido').addEventListener('click', function(){
	  var p = state._presup || {};
	  var payload = {
	    cliente: (_ppCustomerControl && _ppCustomerControl.get_value()) || '',
	    ref: document.getElementById('pp-ped-ref').value,
	    cantidad: p.cantidad || 1,
	    material: document.getElementById('pp-ped-material').value,
	    material_corte: p.material_corte || '',
	    espesor_mm: p.s_mm || 0,
	    densidad_kg_m2: p.densidad_kg_m2 || 0,
	    desarrollo_mm: p.devel_mm || 0,
	    n_pliegues: p.n_pliegues || 0,
	    tonelaje_ton: state.plan ? state.plan.ton.ton : 0,
	    precio_material_unitario: p.costo_mat_unit || 0,
	    precio_plegado_unitario: p.costo_pleg_unit || 0,
	    total_unitario: p.total_unit || 0,
	    total: p.total || 0,
	    segs: state.segs,
	    plan: state.plan,
	    ts: (new Date()).getTime()
	  };
	  var statusEl = document.getElementById('pp-presupStatus');
	  statusEl.className = 'presup-status';
	  statusEl.textContent = 'Guardando...';
	  frappe.call({
	    method: 'sistema_industrial.api.perfiles.guardar_pedido',
	    args: { data_json: JSON.stringify(payload) },
	    callback: function(r){
	      var d = r.message || {};
	      if(d.ok){ statusEl.textContent = '✓ Pedido guardado — ID: ' + d.id; }
	      else { statusEl.className = 'presup-status err'; statusEl.textContent = 'Error: ' + (d.error || 'desconocido'); }
	    },
	    error: function(){
	      statusEl.className = 'presup-status err';
	      statusEl.textContent = 'Error de conexión con el servidor.';
	    }
	  });
	});

	_fetchPrices();
	_fetchMaterials();
}
