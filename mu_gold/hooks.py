app_name = "mu_gold"
app_title = "Mu Gold"
app_publisher = "Mu Gold"
app_description = "Mu Gold"
app_email = "nada.khaled031.nk@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "mu_gold",
# 		"logo": "/assets/mu_gold/logo.png",
# 		"title": "Mu Gold",
# 		"route": "/mu_gold",
# 		"has_permission": "mu_gold.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/mu_gold/css/mu_gold.css"
# app_include_js = "/assets/mu_gold/js/mu_gold.js"

# include js, css files in header of web template
# web_include_css = "/assets/mu_gold/css/mu_gold.css"
# web_include_js = "/assets/mu_gold/js/mu_gold.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "mu_gold/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Sales Invoice" : "public/js/sales_invoice.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "mu_gold/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "mu_gold.utils.jinja_methods",
# 	"filters": "mu_gold.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "mu_gold.install.before_install"
# after_install = "mu_gold.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "mu_gold.uninstall.before_uninstall"
# after_uninstall = "mu_gold.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "mu_gold.utils.before_app_install"
# after_app_install = "mu_gold.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "mu_gold.utils.before_app_uninstall"
# after_app_uninstall = "mu_gold.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mu_gold.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Invoice": {
		"validate": "mu_gold.mu_gold.controllers.sales_invoice.validate",
		"on_submit": "mu_gold.mu_gold.controllers.sales_invoice.on_submit",
		"on_cancel": "mu_gold.mu_gold.controllers.sales_invoice.on_cancel"
	},
	"Gold Receipt": {
		"validate": "mu_gold.mu_gold.controllers.gold_receipt.validate",
		"on_submit": "mu_gold.mu_gold.controllers.gold_receipt.on_submit",
		"on_cancel": "mu_gold.mu_gold.controllers.gold_receipt.on_cancel"
	},
	"Stock Entry": {
		"validate": "mu_gold.mu_gold.controllers.stock_entry.validate"
	},
	"Item": {
		"validate": "mu_gold.mu_gold.controllers.gold_movement_utils.validate_item"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"mu_gold.tasks.all"
# 	],
# 	"daily": [
# 		"mu_gold.tasks.daily"
# 	],
# 	"hourly": [
# 		"mu_gold.tasks.hourly"
# 	],
# 	"weekly": [
# 		"mu_gold.tasks.weekly"
# 	],
# 	"monthly": [
# 		"mu_gold.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "mu_gold.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "mu_gold.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "mu_gold.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["mu_gold.utils.before_request"]
# after_request = ["mu_gold.utils.after_request"]

# Job Events
# ----------
# before_job = ["mu_gold.utils.before_job"]
# after_job = ["mu_gold.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"mu_gold.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

# Fixtures
# --------
# These records are exported to JSON and re-imported on every bench migrate
# fixtures = [
#     {
#         "dt": "Custom Field",
#         "filters": [
#             ["dt", "=", "Sales Invoice"],
#             ["fieldname", "in", [
#                 "is_gold_invoice",
#                 "gold_section",
#                 "gold_item",
#                 "gold_carat",
#                 "gold_weight",
#                 "equivalent_21",
#                 "gold_col_break",
#                 "price_per_gram",
#                 "total_workmanship",
#                 "source_warehouse",
#                 "target_warehouse",
#                 "gold_status_section",
#                 "gold_movement_created",
#                 "gold_movement_status",
#                 "gold_col_break_2",
#                 "stock_entry_ref",
#                 "journal_entry_ref",
#             ]],
#         ]
#     },
# ]

# Export the Gold workspace so it is auto-imported on bench migrate
fixtures = [
    {
        "dt": "Workspace",
        "filters": [["name", "=", "Gold Management"]]
    }
]
