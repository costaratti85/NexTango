frappe.pages["plegados-complejos"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Plegados Complejos",
        single_column: true,
    });
    // Vega: montar la UI aquí usando page.$body
    // API disponible:
    //   sistema_industrial.api.plegados.calcular
    //   sistema_industrial.api.plegados.guardar_pedido
    //   sistema_industrial.api.plegados.list_pedidos
    //   sistema_industrial.api.plegados.get_pedido
    //   sistema_industrial.api.plegados.descargar_dxf (URL directa)
    $(wrapper).find(".page-content").html(frappe.render_template("plegados_complejos"));
};
