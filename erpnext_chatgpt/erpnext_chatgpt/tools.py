import frappe
import json
from datetime import datetime, date, timedelta
from decimal import Decimal


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, timedelta):
        return str(obj)
    frappe.log_error(
        title="Not serializable", message=f"Type {type(obj)} not serializable"
    )
    try:
        return str(obj)
    except Exception:
        return ""


def get_sales_invoices(start_date=None, end_date=None):
    filters = {}
    if start_date and end_date:
        filters['posting_date'] = ['between', [start_date, end_date]]

    invoices = frappe.db.get_all(
        'Sales Invoice',
        filters=filters,
        fields=['*']
    )
    return json.dumps(invoices, default=json_serial)

get_sales_invoices_tool = {
    "type": "function",
    "function": {
        "name": "get_sales_invoices",
        "description": "Get sales invoices from the last month",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
}


def get_sales_invoice(invoice_number):
    invoice = frappe.db.get_value(
        'Sales Invoice',
        invoice_number,
        '*',
        as_dict=True
    )
    return json.dumps([invoice] if invoice else [], default=json_serial)


get_sales_invoice_tool = {
    "type": "function",
    "function": {
        "name": "get_sales_invoice",
        "description": "Get a sales invoice by invoice number",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_number": {
                    "type": "string",
                    "description": "Invoice number",
                },
            },
            "required": ["invoice_number"],
        },
    },
}


def get_employees(department=None, designation=None):
    filters = {}
    if department:
        filters['department'] = department
    if designation:
        filters['designation'] = designation

    employees = frappe.db.get_all(
        'Employee',
        filters=filters,
        fields=['*']
    )
    return json.dumps(employees, default=json_serial)


get_employees_tool = {
    "type": "function",
    "function": {
        "name": "get_employees",
        "description": "Get a list of employees",
        "parameters": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "Department",
                },
                "designation": {
                    "type": "string",
                    "description": "Designation",
                },
            },
            "required": [],
        },
    },
}


def get_purchase_orders(start_date=None, end_date=None, supplier=None):
    filters = {}
    if start_date and end_date:
        filters['transaction_date'] = ['between', [start_date, end_date]]
    if supplier:
        filters['supplier'] = supplier

    purchase_orders = frappe.db.get_all(
        'Purchase Order',
        filters=filters,
        fields=['*']
    )
    return json.dumps(purchase_orders, default=json_serial)


get_purchase_orders_tool = {
    "type": "function",
    "function": {
        "name": "get_purchase_orders",
        "description": "Get purchase orders from the last month",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
                "supplier": {
                    "type": "string",
                    "description": "Supplier name",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
}


def get_customers(customer_name=None):
    filters = {}
    if customer_name:
        # Use partial match for customer name search
        filters['customer_name'] = ['like', f'%{customer_name}%']

    customers = frappe.db.get_all(
        'Customer',
        filters=filters,
        fields=['*']
    )
    return json.dumps(customers, default=json_serial)


get_customers_tool = {
    "type": "function",
    "function": {
        "name": "get_customers",
        "description": "Get a list of customers by name",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer name to search for (partial match supported)",
                },
            },
            "required": [],
        },
    },
}


def get_stock_levels(item_code=None):
    filters = {}
    if item_code:
        filters['item_code'] = item_code

    stock_levels = frappe.db.get_all(
        'Bin',
        filters=filters,
        fields=['item_code', 'warehouse', 'actual_qty']
    )
    return json.dumps(stock_levels, default=json_serial)


get_stock_levels_tool = {
    "type": "function",
    "function": {
        "name": "get_stock_levels",
        "description": "Get current stock levels",
        "parameters": {
            "type": "object",
            "properties": {
                "item_code": {
                    "type": "string",
                    "description": "Item code",
                },
            },
            "required": [],
        },
    },
}


def get_general_ledger_entries(start_date=None, end_date=None, account=None):
    filters = {}
    if start_date and end_date:
        filters['posting_date'] = ['between', [start_date, end_date]]
    if account:
        filters['account'] = account

    gl_entries = frappe.db.get_all(
        'GL Entry',
        filters=filters,
        fields=['*']
    )
    return json.dumps(gl_entries, default=json_serial)


get_general_ledger_entries_tool = {
    "type": "function",
    "function": {
        "name": "get_general_ledger_entries",
        "description": "Get general ledger entries from the last month",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
                "account": {
                    "type": "string",
                    "description": "Account name",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
}


def get_profit_and_loss_statement(
    period_start_date=None, period_end_date=None, periodicity=None
):
    if not period_start_date or not period_end_date or not periodicity:
        return json.dumps(
            {
                "error": "period_start_date, periodicity and period_end_date are required"
            },
            default=json_serial,
        )

    report = frappe.get_doc("Report", "Profit and Loss Statement")
    filters = {
        "period_start_date": period_start_date,
        "period_end_date": period_end_date,
        "periodicity": periodicity,
        "company": frappe.defaults.get_user_default("company"),
    }


get_profit_and_loss_statement_tool = {
    "type": "function",
    "function": {
        "name": "get_profit_and_loss_statement",
        "description": "Get the profit and loss statement report",
        "parameters": {
            "type": "object",
            "properties": {
                "period_start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "period_end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
                "periodicity": {
                    "type": "string",
                    "description": "Periodicity of the report (e.g., Monthly, Quarterly, Yearly, Half-Yearly)",
                },
            },
            "required": ["period_start_date", "period_end_date", "periodicity"],
        },
    },
}


def get_outstanding_invoices(customer=None):
    filters = {'outstanding_amount': ['>', 0]}
    if customer:
        filters['customer'] = customer

    invoices = frappe.db.get_all(
        'Sales Invoice',
        filters=filters,
        fields=['*']
    )
    return json.dumps(invoices, default=json_serial)


get_outstanding_invoices_tool = {
    "type": "function",
    "function": {
        "name": "get_outstanding_invoices",
        "description": "Get the list of outstanding invoices",
        "parameters": {
            "type": "object",
            "properties": {
                "customer": {
                    "type": "string",
                    "description": "Customer name",
                },
            },
            "required": [],
        },
    },
}

def get_sales_orders(start_date=None, end_date=None, customer=None):
    filters = {}
    if start_date and end_date:
        filters['transaction_date'] = ['between', [start_date, end_date]]
    if customer:
        filters['customer'] = customer

    sales_orders = frappe.db.get_all(
        'Sales Order',
        filters=filters,
        fields=['*']
    )
    return json.dumps(sales_orders, default=json_serial)


get_sales_orders_tool = {
    "type": "function",
    "function": {
        "name": "get_sales_orders",
        "description": "Get sales orders from the last month",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
                "customer": {
                    "type": "string",
                    "description": "Customer name",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
}


def get_purchase_invoices(start_date=None, end_date=None, supplier=None):
    filters = {}
    if start_date and end_date:
        filters['posting_date'] = ['between', [start_date, end_date]]
    if supplier:
        filters['supplier'] = supplier

    purchase_invoices = frappe.db.get_all(
        'Purchase Invoice',
        filters=filters,
        fields=['*']
    )
    return json.dumps(purchase_invoices, default=json_serial)



get_purchase_invoices_tool = {
    "type": "function",
    "function": {
        "name": "get_purchase_invoices",
        "description": "Get purchase invoices from the last month",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
                "supplier": {
                    "type": "string",
                    "description": "Supplier name",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
}


def get_journal_entries(start_date=None, end_date=None):
    filters = {}
    if start_date and end_date:
        filters['posting_date'] = ['between', [start_date, end_date]]

    journal_entries = frappe.db.get_all(
        'Journal Entry',
        filters=filters,
        fields=['*']
    )
    return json.dumps(journal_entries, default=json_serial)


get_journal_entries_tool = {
    "type": "function",
    "function": {
        "name": "get_journal_entries",
        "description": "Get journal entries from the last month",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
}


def get_payments(start_date=None, end_date=None, payment_type=None):
    filters = {}
    if start_date and end_date:
        filters['posting_date'] = ['between', [start_date, end_date]]
    if payment_type:
        filters['payment_type'] = payment_type

    payment_entries = frappe.db.get_all(
        'Payment Entry',
        filters=filters,
        fields=['*']
    )
    return json.dumps(payment_entries, default=json_serial)


get_payments_tool = {
    "type": "function",
    "function": {
        "name": "get_payments",
        "description": "Get payment entries from the last month",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
                "payment_type": {
                    "type": "string",
                    "description": "Payment type (e.g., Receive, Pay)",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
}


def get_tools():
    return [
        get_sales_invoices_tool,
        get_sales_invoice_tool,
        get_employees_tool,
        get_purchase_orders_tool,
        get_customers_tool,
        get_stock_levels_tool,
        get_general_ledger_entries_tool,
        get_profit_and_loss_statement_tool,
        get_outstanding_invoices_tool,
        get_sales_orders_tool,
        get_purchase_invoices_tool,
        get_journal_entries_tool,
        get_payments_tool,
    ]


available_functions = {
    "get_sales_invoices": get_sales_invoices,
    "get_sales_invoice": get_sales_invoice,
    "get_employees": get_employees,
    "get_purchase_orders": get_purchase_orders,
    "get_customers": get_customers,
    "get_stock_levels": get_stock_levels,
    "get_general_ledger_entries": get_general_ledger_entries,
    "get_profit_and_loss_statement": get_profit_and_loss_statement,
    "get_outstanding_invoices": get_outstanding_invoices,
    "get_sales_orders": get_sales_orders,
    "get_purchase_invoices": get_purchase_invoices,
    "get_journal_entries": get_journal_entries,
    "get_payments": get_payments,
}
