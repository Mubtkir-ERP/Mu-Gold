import frappe

def execute():
    # Find all Workspaces matching %Gold%
    workspaces = frappe.get_all("Workspace", filters={"title": ("like", "%Gold%")}, fields=["name", "title", "module", "public"])
    print("Found Gold Workspaces:")
    for w in workspaces:
        print(f"- {w.name} (Title: {w.title}, Module: {w.module}, Public: {w.public})")

    if len(workspaces) <= 1:
        print("Only one or zero Gold workspaces found. Nothing to delete.")
        return

    deleted = 0
    # Keep only "Gold Management", delete everything else matching "Gold"
    for w in workspaces:
        if w.name != "Gold Management":
            frappe.delete_doc("Workspace", w.name)
            print(f"Deleted duplicate workspace: {w.name}")
            deleted += 1

    frappe.db.commit()
    print("Workspace cleanup completed. Deleted:", deleted)
