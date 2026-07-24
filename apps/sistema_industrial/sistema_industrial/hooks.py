app_name = "sistema_industrial"
app_title = "Sistema Industrial"
app_publisher = "SistemaIndustrial"
app_description = "Industrial integration app over ERPNext"
app_email = "costaratti@gmail.com"
app_license = "MIT"

# CSS común de las páginas del módulo (scopeado bajo .si-page — ver el archivo)
app_include_css = "/assets/sistema_industrial/css/sistema_industrial.css"

# version_stamp.js: generado por deploy.generate_version_stamp() en cada
# deploy, ANTES de bench build (no commiteado — ver .gitignore). Va primero
# en la lista porque version_footer.js lee window.SI_VERSION al cargar.
app_include_js = [
    "/assets/sistema_industrial/js/version_stamp.js",
    "/assets/sistema_industrial/js/version_footer.js",
    # Helper compartido: botón "Actualizar" de sync manual de clientes (MSG_023)
    "/assets/sistema_industrial/js/customer_sync.js",
]

fixtures = [
    {"dt": "Role", "filters": [["role_name", "like", "SI %"]]},
]

# Custom fields declarados por código (idempotentes) — se crean en cada migrate.
# ocr_suppliers.si_ocr_layout (Supplier): layout aprendido del OCR de proveedores.
# + Aditivo e idempotente: suma el link a la página OCR Proveedores dentro del
#   workspace estándar "Buying" (Compras). Se re-aplica tras cada migrate → sobrevive
#   a updates de ERPNext sin forkear el buying.json estándar.
after_migrate = [
    "sistema_industrial.ocr_suppliers.custom_fields.ensure_ocr_custom_fields",
    # Sistema Industrial visible en la grilla de la home del Desk (type=Workspace).
    "sistema_industrial.ocr_suppliers.buying_workspace.ensure_sistema_industrial_on_home",
    # OCR Proveedores dentro del workspace estándar Compras (Buying).
    "sistema_industrial.ocr_suppliers.buying_workspace.add_ocr_link_to_buying",
]

# Baja de stock por ventas de Tango (T5). DORMIDO mientras el gate
# `ocr_baja_auto_submit` esté OFF (scheduled_baja_ventas no procesa nada). Se
# despierta al prender el gate tras el smoke duro. Read-only sobre Tango.
scheduler_events = {
    "cron": {
        # cada 15 min; idempotente por el dedup (HWM + tango_comprobante_ref único).
        "*/15 * * * *": [
            "sistema_industrial.ocr_suppliers.baja_orchestrator.scheduled_baja_ventas",
        ],
    },
}
