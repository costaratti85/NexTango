app_name = "sistema_industrial"
app_title = "Sistema Industrial"
app_publisher = "SistemaIndustrial"
app_description = "Industrial integration app over ERPNext"
app_email = "costaratti@gmail.com"
app_license = "MIT"

scheduler_events = {
    "daily": [
        "sistema_industrial.tango_sync.scheduled.sync_customers_from_tango",
        "sistema_industrial.tango_sync.scheduled.sync_articles_from_tango",
    ],
}
