import frappe

def execute():
    meta = frappe.get_meta("Sales Invoice")
    for d in meta.fields:
        print(f"{d.fieldname} | {d.label} | {d.fieldtype}")
