frappe.query_reports["Gold Customer Statement"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("الشركة"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "customer",
			"label": __("العميل"),
			"fieldtype": "Link",
			"options": "Customer",
			"reqd": 1
		},
		{
			"fieldname": "from_date",
			"label": __("من تاريخ"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("إلى تاريخ"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	],

	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Highlight totals and opening rows in bold
		if (data && data.bold) {
			value = `<strong>${value}</strong>`;
		}

		// Color debit columns orange
		if (column.fieldname === "debit_weight" || column.fieldname === "debit_21") {
			if (data && (data.debit_21 || data.debit_weight)) {
				value = `<span style="color: #e67e22; font-weight: 600;">${value}</span>`;
			}
		}

		// Color credit columns green
		if (column.fieldname === "credit_weight" || column.fieldname === "credit_21") {
			if (data && (data.credit_21 || data.credit_weight)) {
				value = `<span style="color: #27ae60; font-weight: 600;">${value}</span>`;
			}
		}

		// Color balance column blue
		if (column.fieldname === "balance_21" && data && data.balance_21 !== undefined && data.balance_21 !== null) {
			let color = data.balance_21 >= 0 ? "#2980b9" : "#c0392b";
			value = `<span style="color: ${color}; font-weight: 600;">${value}</span>`;
		}

		return value;
	}
};
