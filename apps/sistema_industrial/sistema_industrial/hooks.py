app_name = "sistema_industrial"
app_title = "Sistema Industrial"
app_publisher = "SistemaIndustrial"
app_description = "Industrial integration app over ERPNext"
app_email = "costaratti@gmail.com"
app_license = "MIT"

# CSS común de las páginas del módulo (scopeado bajo .si-page — ver el archivo)
app_include_css = "/assets/sistema_industrial/css/sistema_industrial.css"

# Helper compartido: botón "Actualizar" de sync manual de clientes (MSG_023)
app_include_js = "/assets/sistema_industrial/js/customer_sync.js"

fixtures = [
    {"dt": "Role", "filters": [["role_name", "like", "SI %"]]},
]
