# Copyright (c) 2026, Mu Gold and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class GoldCustomerLedger(Document):
	def on_cancel(self):
		self.db_set('is_cancelled', 1)
