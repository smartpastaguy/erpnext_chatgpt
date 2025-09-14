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


def list_invoices(
    invoice_type="Sales Invoice",
    customer=None,
    supplier=None,
    status=None,
    start_date=None,
    end_date=None,
    min_amount=None,
    max_amount=None,
    is_paid=None,
    sort_by="posting_date",
    sort_order="desc",
    limit=100,
    offset=0
):
    """
    List invoices (Sales or Purchase) with advanced filtering and sorting options
    """
    # Determine the doctype based on invoice_type
    if invoice_type not in ["Sales Invoice", "Purchase Invoice"]:
        return json.dumps({
            "error": "Invalid invoice_type. Must be 'Sales Invoice' or 'Purchase Invoice'"
        }, default=json_serial)

    filters = {}

    # Apply filters based on invoice type
    if invoice_type == "Sales Invoice":
        if customer:
            filters['customer'] = ['like', f'%{customer}%']
    else:  # Purchase Invoice
        if supplier:
            filters['supplier'] = ['like', f'%{supplier}%']

    # Common filters
    if status:
        filters['status'] = status
    if start_date and end_date:
        filters['posting_date'] = ['between', [start_date, end_date]]
    elif start_date:
        filters['posting_date'] = ['>=', start_date]
    elif end_date:
        filters['posting_date'] = ['<=', end_date]

    if min_amount and max_amount:
        filters['grand_total'] = ['between', [min_amount, max_amount]]
    elif min_amount:
        filters['grand_total'] = ['>=', min_amount]
    elif max_amount:
        filters['grand_total'] = ['<=', max_amount]

    if is_paid is not None:
        if is_paid:
            filters['outstanding_amount'] = 0
        else:
            filters['outstanding_amount'] = ['>', 0]

    # Validate sort_by field
    valid_sort_fields = ['name', 'posting_date', 'due_date', 'grand_total',
                        'outstanding_amount', 'status', 'creation', 'modified']
    if sort_by not in valid_sort_fields:
        sort_by = 'posting_date'

    # Build order_by clause
    order_by = f'{sort_by} {sort_order}'

    # Select appropriate fields based on invoice type
    if invoice_type == "Sales Invoice":
        fields = ['name', 'customer', 'customer_name', 'posting_date', 'due_date',
                 'grand_total', 'outstanding_amount', 'status', 'currency',
                 'is_return', 'creation', 'modified']
    else:
        fields = ['name', 'supplier', 'supplier_name', 'posting_date', 'due_date',
                 'grand_total', 'outstanding_amount', 'status', 'currency',
                 'is_return', 'creation', 'modified']

    invoices = frappe.db.get_all(
        invoice_type,
        filters=filters,
        fields=fields,
        order_by=order_by,
        limit_start=offset,
        limit_page_length=limit
    )

    # Get count for pagination
    total_count = frappe.db.count(invoice_type, filters=filters)

    # Calculate summary statistics - simplified approach
    if invoices:
        total_amount = sum(inv.get('grand_total', 0) for inv in invoices)
        total_outstanding = sum(inv.get('outstanding_amount', 0) for inv in invoices)
        average_amount = total_amount / len(invoices) if invoices else 0
        summary = {
            'total_invoices': len(invoices),
            'total_amount': total_amount,
            'total_outstanding': total_outstanding,
            'average_amount': average_amount
        }
    else:
        summary = {
            'total_invoices': 0,
            'total_amount': 0,
            'total_outstanding': 0,
            'average_amount': 0
        }

    return json.dumps({
        'invoice_type': invoice_type,
        'invoices': invoices,
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
        'summary': summary
    }, default=json_serial)


list_invoices_tool = {
    "type": "function",
    "function": {
        "name": "list_invoices",
        "description": "List invoices with advanced filtering, sorting, and pagination",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_type": {
                    "type": "string",
                    "description": "Type of invoice ('Sales Invoice' or 'Purchase Invoice')",
                    "default": "Sales Invoice"
                },
                "customer": {
                    "type": "string",
                    "description": "Filter by customer name (for Sales Invoice, partial match)",
                },
                "supplier": {
                    "type": "string",
                    "description": "Filter by supplier name (for Purchase Invoice, partial match)",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status (Draft, Submitted, Paid, Unpaid, Overdue, Cancelled)",
                },
                "start_date": {
                    "type": "string",
                    "description": "Filter invoices from this date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "Filter invoices until this date (YYYY-MM-DD)",
                },
                "min_amount": {
                    "type": "number",
                    "description": "Minimum invoice amount",
                },
                "max_amount": {
                    "type": "number",
                    "description": "Maximum invoice amount",
                },
                "is_paid": {
                    "type": "boolean",
                    "description": "Filter by payment status (true for fully paid, false for outstanding)",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort by (name, posting_date, due_date, grand_total, outstanding_amount, status)",
                    "default": "posting_date"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sort order (asc/desc)",
                    "default": "desc"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of records to return",
                    "default": 100
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of records to skip",
                    "default": 0
                }
            },
            "required": [],
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


def list_customers(
    customer_name=None,
    customer_group=None,
    territory=None,
    customer_type=None,
    disabled=None,
    sort_by="creation",
    sort_order="desc",
    limit=100,
    offset=0
):
    """
    List customers with advanced filtering and sorting options
    """
    filters = {}

    # Apply filters
    if customer_name:
        filters['customer_name'] = ['like', f'%{customer_name}%']
    if customer_group:
        filters['customer_group'] = customer_group
    if territory:
        filters['territory'] = territory
    if customer_type:
        filters['customer_type'] = customer_type
    if disabled is not None:
        filters['disabled'] = disabled

    # Validate sort_by field
    valid_sort_fields = ['customer_name', 'customer_group', 'territory', 'creation', 'modified']
    if sort_by not in valid_sort_fields:
        sort_by = 'creation'

    # Build order_by clause
    order_by = f'{sort_by} {sort_order}'

    customers = frappe.db.get_all(
        'Customer',
        filters=filters,
        fields=['name', 'customer_name', 'customer_group', 'territory',
                'customer_type', 'disabled', 'creation', 'modified',
                'credit_limit', 'customer_primary_contact', 'customer_primary_address'],
        order_by=order_by,
        limit_start=offset,
        limit_page_length=limit
    )

    # Get count for pagination
    total_count = frappe.db.count('Customer', filters=filters)

    return json.dumps({
        'customers': customers,
        'total_count': total_count,
        'limit': limit,
        'offset': offset
    }, default=json_serial)


list_customers_tool = {
    "type": "function",
    "function": {
        "name": "list_customers",
        "description": "List customers with advanced filtering, sorting, and pagination",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Filter by customer name (partial match)",
                },
                "customer_group": {
                    "type": "string",
                    "description": "Filter by customer group",
                },
                "territory": {
                    "type": "string",
                    "description": "Filter by territory",
                },
                "customer_type": {
                    "type": "string",
                    "description": "Filter by customer type (Company/Individual)",
                },
                "disabled": {
                    "type": "boolean",
                    "description": "Filter by enabled/disabled status",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort by (customer_name, customer_group, territory, creation, modified)",
                    "default": "creation"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sort order (asc/desc)",
                    "default": "desc"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of records to return",
                    "default": 100
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of records to skip",
                    "default": 0
                }
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


def list_quotations(
    customer=None,
    quotation_to=None,
    status=None,
    start_date=None,
    end_date=None,
    valid_till_start=None,
    valid_till_end=None,
    min_amount=None,
    max_amount=None,
    sort_by="transaction_date",
    sort_order="desc",
    limit=100,
    offset=0
):
    """
    List quotations with advanced filtering and sorting options
    """
    filters = {}

    # Apply filters
    if customer:
        filters['party_name'] = ['like', f'%{customer}%']
    if quotation_to:
        filters['quotation_to'] = quotation_to  # 'Customer' or 'Lead'
    if status:
        filters['status'] = status  # Draft, Submitted, Ordered, Lost, Cancelled, Expired

    # Transaction date filters
    if start_date and end_date:
        filters['transaction_date'] = ['between', [start_date, end_date]]
    elif start_date:
        filters['transaction_date'] = ['>=', start_date]
    elif end_date:
        filters['transaction_date'] = ['<=', end_date]

    # Valid till date filters
    if valid_till_start and valid_till_end:
        filters['valid_till'] = ['between', [valid_till_start, valid_till_end]]
    elif valid_till_start:
        filters['valid_till'] = ['>=', valid_till_start]
    elif valid_till_end:
        filters['valid_till'] = ['<=', valid_till_end]

    # Amount filters
    if min_amount and max_amount:
        filters['grand_total'] = ['between', [min_amount, max_amount]]
    elif min_amount:
        filters['grand_total'] = ['>=', min_amount]
    elif max_amount:
        filters['grand_total'] = ['<=', max_amount]

    # Validate sort_by field
    valid_sort_fields = ['name', 'transaction_date', 'valid_till', 'grand_total',
                        'status', 'party_name', 'creation', 'modified']
    if sort_by not in valid_sort_fields:
        sort_by = 'transaction_date'

    # Build order_by clause
    order_by = f'{sort_by} {sort_order}'

    quotations = frappe.db.get_all(
        'Quotation',
        filters=filters,
        fields=['name', 'quotation_to', 'party_name', 'customer_name',
                'transaction_date', 'valid_till', 'grand_total', 'status',
                'currency', 'order_type', 'creation', 'modified'],
        order_by=order_by,
        limit_start=offset,
        limit_page_length=limit
    )

    # Get count for pagination
    total_count = frappe.db.count('Quotation', filters=filters)

    # Calculate summary statistics
    if quotations:
        total_amount = sum(q.get('grand_total', 0) for q in quotations)
        average_amount = total_amount / len(quotations) if quotations else 0
        summary = {
            'total_quotations': len(quotations),
            'total_amount': total_amount,
            'average_amount': average_amount
        }
    else:
        summary = {
            'total_quotations': 0,
            'total_amount': 0,
            'average_amount': 0
        }

    return json.dumps({
        'quotations': quotations,
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
        'summary': summary
    }, default=json_serial)


list_quotations_tool = {
    "type": "function",
    "function": {
        "name": "list_quotations",
        "description": "List quotations with advanced filtering, sorting, and pagination",
        "parameters": {
            "type": "object",
            "properties": {
                "customer": {
                    "type": "string",
                    "description": "Filter by customer/lead name (partial match)",
                },
                "quotation_to": {
                    "type": "string",
                    "description": "Filter by quotation type ('Customer' or 'Lead')",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status (Draft, Submitted, Ordered, Lost, Cancelled, Expired)",
                },
                "start_date": {
                    "type": "string",
                    "description": "Filter quotations from this transaction date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "Filter quotations until this transaction date (YYYY-MM-DD)",
                },
                "valid_till_start": {
                    "type": "string",
                    "description": "Filter by minimum validity date (YYYY-MM-DD)",
                },
                "valid_till_end": {
                    "type": "string",
                    "description": "Filter by maximum validity date (YYYY-MM-DD)",
                },
                "min_amount": {
                    "type": "number",
                    "description": "Minimum quotation amount",
                },
                "max_amount": {
                    "type": "number",
                    "description": "Maximum quotation amount",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort by (name, transaction_date, valid_till, grand_total, status, party_name)",
                    "default": "transaction_date"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sort order (asc/desc)",
                    "default": "desc"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of records to return",
                    "default": 100
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of records to skip",
                    "default": 0
                }
            },
            "required": [],
        },
    },
}


def list_sales_orders(
    customer=None,
    status=None,
    delivery_status=None,
    billing_status=None,
    start_date=None,
    end_date=None,
    delivery_date_start=None,
    delivery_date_end=None,
    min_amount=None,
    max_amount=None,
    sort_by="transaction_date",
    sort_order="desc",
    limit=100,
    offset=0
):
    """
    List sales orders with advanced filtering and sorting options
    """
    filters = {}

    # Apply filters
    if customer:
        filters['customer'] = ['like', f'%{customer}%']
    if status:
        filters['status'] = status  # Draft, To Deliver and Bill, To Bill, To Deliver, Completed, Cancelled, Closed
    if delivery_status:
        filters['delivery_status'] = delivery_status  # Not Delivered, Fully Delivered, Partly Delivered, Closed, Not Applicable
    if billing_status:
        filters['billing_status'] = billing_status  # Not Billed, Fully Billed, Partly Billed, Closed

    # Transaction date filters
    if start_date and end_date:
        filters['transaction_date'] = ['between', [start_date, end_date]]
    elif start_date:
        filters['transaction_date'] = ['>=', start_date]
    elif end_date:
        filters['transaction_date'] = ['<=', end_date]

    # Delivery date filters
    if delivery_date_start and delivery_date_end:
        filters['delivery_date'] = ['between', [delivery_date_start, delivery_date_end]]
    elif delivery_date_start:
        filters['delivery_date'] = ['>=', delivery_date_start]
    elif delivery_date_end:
        filters['delivery_date'] = ['<=', delivery_date_end]

    # Amount filters
    if min_amount and max_amount:
        filters['grand_total'] = ['between', [min_amount, max_amount]]
    elif min_amount:
        filters['grand_total'] = ['>=', min_amount]
    elif max_amount:
        filters['grand_total'] = ['<=', max_amount]

    # Validate sort_by field
    valid_sort_fields = ['name', 'transaction_date', 'delivery_date', 'grand_total',
                        'status', 'customer', 'per_delivered', 'per_billed', 'creation', 'modified']
    if sort_by not in valid_sort_fields:
        sort_by = 'transaction_date'

    # Build order_by clause
    order_by = f'{sort_by} {sort_order}'

    sales_orders = frappe.db.get_all(
        'Sales Order',
        filters=filters,
        fields=['name', 'customer', 'customer_name', 'transaction_date', 'delivery_date',
                'grand_total', 'status', 'delivery_status', 'billing_status',
                'per_delivered', 'per_billed', 'currency', 'order_type',
                'creation', 'modified'],
        order_by=order_by,
        limit_start=offset,
        limit_page_length=limit
    )

    # Get count for pagination
    total_count = frappe.db.count('Sales Order', filters=filters)

    # Calculate summary statistics
    if sales_orders:
        total_amount = sum(so.get('grand_total', 0) for so in sales_orders)
        average_amount = total_amount / len(sales_orders) if sales_orders else 0
        avg_delivery = sum(so.get('per_delivered', 0) for so in sales_orders) / len(sales_orders)
        avg_billed = sum(so.get('per_billed', 0) for so in sales_orders) / len(sales_orders)
        summary = {
            'total_orders': len(sales_orders),
            'total_amount': total_amount,
            'average_amount': average_amount,
            'average_delivery_percentage': avg_delivery,
            'average_billing_percentage': avg_billed
        }
    else:
        summary = {
            'total_orders': 0,
            'total_amount': 0,
            'average_amount': 0,
            'average_delivery_percentage': 0,
            'average_billing_percentage': 0
        }

    return json.dumps({
        'sales_orders': sales_orders,
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
        'summary': summary
    }, default=json_serial)


list_sales_orders_tool = {
    "type": "function",
    "function": {
        "name": "list_sales_orders",
        "description": "List sales orders with advanced filtering, sorting, and pagination",
        "parameters": {
            "type": "object",
            "properties": {
                "customer": {
                    "type": "string",
                    "description": "Filter by customer name (partial match)",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by order status",
                },
                "delivery_status": {
                    "type": "string",
                    "description": "Filter by delivery status (Not Delivered, Fully Delivered, Partly Delivered, etc.)",
                },
                "billing_status": {
                    "type": "string",
                    "description": "Filter by billing status (Not Billed, Fully Billed, Partly Billed, Closed)",
                },
                "start_date": {
                    "type": "string",
                    "description": "Filter orders from this transaction date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "Filter orders until this transaction date (YYYY-MM-DD)",
                },
                "delivery_date_start": {
                    "type": "string",
                    "description": "Filter by minimum delivery date (YYYY-MM-DD)",
                },
                "delivery_date_end": {
                    "type": "string",
                    "description": "Filter by maximum delivery date (YYYY-MM-DD)",
                },
                "min_amount": {
                    "type": "number",
                    "description": "Minimum order amount",
                },
                "max_amount": {
                    "type": "number",
                    "description": "Maximum order amount",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort by (name, transaction_date, delivery_date, grand_total, status, customer, per_delivered, per_billed)",
                    "default": "transaction_date"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sort order (asc/desc)",
                    "default": "desc"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of records to return",
                    "default": 100
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of records to skip",
                    "default": 0
                }
            },
            "required": [],
        },
    },
}


def list_delivery_notes(
    customer=None,
    status=None,
    serial_number=None,
    item_code=None,
    start_date=None,
    end_date=None,
    lr_no=None,  # Lorry Receipt Number / Tracking Number
    transporter=None,
    sort_by="posting_date",
    sort_order="desc",
    limit=100,
    offset=0
):
    """
    List delivery notes with advanced filtering, sorting options, and serial number search
    """
    filters = {}

    # Handle serial number search - first find Serial and Batch Bundle, then filter
    if serial_number:
        # Step 1: Find Serial and Batch Bundle containing the serial number
        serial_bundles = frappe.db.get_all(
            'Serial and Batch Entry',
            filters={
                'serial_no': ['like', f'%{serial_number}%']
            },
            fields=['parent'],
            distinct=True
        )

        if serial_bundles:
            # Extract bundle names
            bundle_names = [bundle.parent for bundle in serial_bundles]

            # Step 2: Find delivery notes containing these bundles
            delivery_note_items = frappe.db.get_all(
                'Delivery Note Item',
                filters={
                    'serial_and_batch_bundle': ['in', bundle_names]
                },
                fields=['parent'],
                distinct=True
            )

            if delivery_note_items:
                # Extract parent names from result
                note_names = [item.parent for item in delivery_note_items]
                filters['name'] = ['in', note_names]
            else:
                # No delivery notes found with this serial number
                return json.dumps({
                    'delivery_notes': [],
                    'total_count': 0,
                    'limit': limit,
                    'offset': offset,
                    'summary': {
                        'total_notes': 0,
                        'total_amount': 0,
                        'average_amount': 0
                    }
                }, default=json_serial)
        else:
            # No serial bundles found with this serial number
            return json.dumps({
                'delivery_notes': [],
                'total_count': 0,
                'limit': limit,
                'offset': offset,
                'summary': {
                    'total_notes': 0,
                    'total_amount': 0,
                    'average_amount': 0
                }
            }, default=json_serial)

    # Apply other filters
    if customer:
        filters['customer'] = ['like', f'%{customer}%']
    if status:
        filters['status'] = status  # Draft, To Bill, Completed, Cancelled, Closed
    if lr_no:
        filters['lr_no'] = ['like', f'%{lr_no}%']
    if transporter:
        filters['transporter'] = ['like', f'%{transporter}%']

    # Date filters
    if start_date and end_date:
        filters['posting_date'] = ['between', [start_date, end_date]]
    elif start_date:
        filters['posting_date'] = ['>=', start_date]
    elif end_date:
        filters['posting_date'] = ['<=', end_date]

    # Item code filter - using Frappe database API
    if item_code and not serial_number:  # If serial_number is already filtered, skip item_code
        item_filter_notes = frappe.db.get_all(
            'Delivery Note Item',
            filters={'item_code': item_code},
            fields=['parent'],
            distinct=True
        )

        if item_filter_notes:
            item_note_names = [note.parent for note in item_filter_notes]
            if 'name' in filters:
                # Intersect with existing name filter
                existing_names = filters['name'][1]
                filters['name'] = ['in', list(set(existing_names) & set(item_note_names))]
            else:
                filters['name'] = ['in', item_note_names]
        else:
            # No delivery notes found with this item
            return json.dumps({
                'delivery_notes': [],
                'total_count': 0,
                'limit': limit,
                'offset': offset,
                'summary': {
                    'total_notes': 0,
                    'total_amount': 0,
                    'average_amount': 0
                }
            }, default=json_serial)

    # Validate sort_by field
    valid_sort_fields = ['name', 'posting_date', 'customer', 'grand_total',
                        'status', 'per_billed', 'creation', 'modified']
    if sort_by not in valid_sort_fields:
        sort_by = 'posting_date'

    # Build order_by clause
    order_by = f'{sort_by} {sort_order}'

    delivery_notes = frappe.db.get_all(
        'Delivery Note',
        filters=filters,
        fields=['name', 'customer', 'customer_name', 'posting_date',
                'grand_total', 'status', 'per_billed', 'currency',
                'lr_no', 'lr_date', 'transporter', 'vehicle_no',
                'is_return', 'creation', 'modified'],
        order_by=order_by,
        limit_start=offset,
        limit_page_length=limit
    )

    # If serial number was searched, add serial number info to results
    if serial_number and delivery_notes:
        for note in delivery_notes:
            # Get items with the matching serial and batch bundle using Frappe Query Builder
            from frappe.query_builder import DocType

            DeliveryNoteItem = DocType('Delivery Note Item')
            SerialBatchEntry = DocType('Serial and Batch Entry')

            # Get delivery note items with their bundles
            items = frappe.db.get_all(
                'Delivery Note Item',
                filters={'parent': note['name']},
                fields=['item_code', 'item_name', 'serial_and_batch_bundle', 'qty']
            )

            matched_items = []
            for item in items:
                if item.serial_and_batch_bundle:
                    # Get serial numbers from the bundle
                    serials = frappe.db.get_all(
                        'Serial and Batch Entry',
                        filters={
                            'parent': item.serial_and_batch_bundle,
                            'serial_no': ['like', f'%{serial_number}%']
                        },
                        fields=['serial_no']
                    )
                    if serials:
                        item['serial_numbers'] = ', '.join([s.serial_no for s in serials])
                        matched_items.append(item)

            note['matched_serial_items'] = matched_items

    # Get count for pagination
    total_count = frappe.db.count('Delivery Note', filters=filters)

    # Calculate summary statistics
    if delivery_notes:
        total_amount = sum(dn.get('grand_total', 0) for dn in delivery_notes)
        average_amount = total_amount / len(delivery_notes) if delivery_notes else 0
        avg_billed = sum(dn.get('per_billed', 0) for dn in delivery_notes) / len(delivery_notes)
        summary = {
            'total_notes': len(delivery_notes),
            'total_amount': total_amount,
            'average_amount': average_amount,
            'average_billing_percentage': avg_billed
        }
    else:
        summary = {
            'total_notes': 0,
            'total_amount': 0,
            'average_amount': 0,
            'average_billing_percentage': 0
        }

    return json.dumps({
        'delivery_notes': delivery_notes,
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
        'summary': summary
    }, default=json_serial)


list_delivery_notes_tool = {
    "type": "function",
    "function": {
        "name": "list_delivery_notes",
        "description": "List delivery notes with advanced filtering, sorting, pagination, and serial number search",
        "parameters": {
            "type": "object",
            "properties": {
                "customer": {
                    "type": "string",
                    "description": "Filter by customer name (partial match)",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status (Draft, To Bill, Completed, Cancelled, Closed)",
                },
                "serial_number": {
                    "type": "string",
                    "description": "Search for delivery notes containing this serial number (partial match)",
                },
                "item_code": {
                    "type": "string",
                    "description": "Filter by item code in delivery note items",
                },
                "start_date": {
                    "type": "string",
                    "description": "Filter notes from this posting date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "Filter notes until this posting date (YYYY-MM-DD)",
                },
                "lr_no": {
                    "type": "string",
                    "description": "Filter by Lorry Receipt Number / Tracking Number (partial match)",
                },
                "transporter": {
                    "type": "string",
                    "description": "Filter by transporter name (partial match)",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort by (name, posting_date, customer, grand_total, status, per_billed)",
                    "default": "posting_date"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sort order (asc/desc)",
                    "default": "desc"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of records to return",
                    "default": 100
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of records to skip",
                    "default": 0
                }
            },
            "required": [],
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
        list_invoices_tool,
        get_employees_tool,
        get_purchase_orders_tool,
        get_customers_tool,
        list_customers_tool,
        get_stock_levels_tool,
        get_general_ledger_entries_tool,
        get_profit_and_loss_statement_tool,
        get_outstanding_invoices_tool,
        get_sales_orders_tool,
        list_quotations_tool,
        list_sales_orders_tool,
        list_delivery_notes_tool,
        get_purchase_invoices_tool,
        get_journal_entries_tool,
        get_payments_tool,
    ]


available_functions = {
    "get_sales_invoices": get_sales_invoices,
    "get_sales_invoice": get_sales_invoice,
    "list_invoices": list_invoices,
    "get_employees": get_employees,
    "get_purchase_orders": get_purchase_orders,
    "get_customers": get_customers,
    "list_customers": list_customers,
    "get_stock_levels": get_stock_levels,
    "get_general_ledger_entries": get_general_ledger_entries,
    "get_profit_and_loss_statement": get_profit_and_loss_statement,
    "get_outstanding_invoices": get_outstanding_invoices,
    "get_sales_orders": get_sales_orders,
    "list_quotations": list_quotations,
    "list_sales_orders": list_sales_orders,
    "list_delivery_notes": list_delivery_notes,
    "get_purchase_invoices": get_purchase_invoices,
    "get_journal_entries": get_journal_entries,
    "get_payments": get_payments,
}
