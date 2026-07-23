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
after_migrate = [
    "sistema_industrial.ocr_suppliers.custom_fields.ensure_ocr_custom_fields",
]
