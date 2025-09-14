# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- **Install app on ERPNext site**: `bench --site [site-name] install-app erpnext_chatgpt`
- **Restart bench**: `bench restart`
- **Clear cache**: `bench clear-cache`
- **Console access**: `bench console` (for Python/ERPNext shell)
- **Migrate database**: `bench --site [site-name] migrate`

### Testing
- **Run doctests**: `bench --site [site-name] run-tests --app erpnext_chatgpt`
- **Test specific doctype**: `bench --site [site-name] run-tests --doctype "OpenAI Settings"`

## Architecture

This is an ERPNext app that integrates OpenAI capabilities into the ERPNext ERP system. Key architectural components:

### Core Structure
- **Frappe Framework Integration**: Built on top of Frappe/ERPNext framework, using its ORM, API patterns, and whitelisting mechanisms
- **OpenAI Client**: Uses OpenAI Python SDK v1.32.0 for GPT-4 model interactions
- **Tool System**: Implements function calling with 14+ ERPNext-specific tools for data retrieval (sales invoices, employees, stock levels, etc.)

### Key Files
- `erpnext_chatgpt/api.py`: Main API endpoints for OpenAI integration
  - Handles conversation management with configurable token limiting
  - Model selection from settings (gpt-3.5-turbo, gpt-4, etc.)
  - Implements tool calling system for ERPNext data queries
  - Manages OpenAI client initialization and API key validation

- `erpnext_chatgpt/tools.py`: Defines available ERPNext functions
  - Each function queries ERPNext database directly via SQL
  - Includes JSON serialization for ERPNext data types
  - Functions mapped to OpenAI tool definitions

- `public/js/frontend.js`: Client-side JavaScript for chat interface
  - Integrates with ERPNext desk environment
  - Manages session creation and conversation state
  - Handles UI for chat dialog

### Frontend Integration
- JavaScript loaded via `hooks.py` configuration
- Chat button injected into ERPNext navbar for System Managers
- Session-based conversation management with localStorage

### Database Interaction
- Direct SQL queries to ERPNext tables (tabSales Invoice, tabEmployee, etc.)
- Uses Frappe's database abstraction layer (`frappe.db.sql`)
- Custom JSON serializer for Decimal, datetime, and timedelta types

### Security Model
- API endpoints whitelisted via `@frappe.whitelist()` decorator
- System Manager role required for access
- API key stored in OpenAI Settings DocType (single document)

## ERPNext App Conventions
- Module structure follows ERPNext patterns (doctype, config, hooks)
- Uses Frappe's logging system for error tracking
- Fixtures defined for OpenAI Settings DocType deployment
- Client-side code uses Frappe's dialog and notification systems

## Adding New Tools

To add new tools for OpenAI function calling, follow these steps:

### 1. Define the Function in `tools.py`

Create a new function that queries ERPNext data. For list commands, include these standard parameters:

```python
def list_your_doctype(
    # Filter parameters
    field1=None,
    field2=None,
    status=None,
    date_from=None,
    date_to=None,

    # Sorting parameters
    sort_by='creation',  # Default sort field
    sort_order='desc',   # 'asc' or 'desc'

    # Pagination
    limit=10,
    offset=0,

    # Special filters (if applicable)
    search_text=None,    # For text search across multiple fields
    item_code=None,      # For filtering by specific items
    serial_number=None   # For serial number tracking
):
    """
    List documents with filtering, sorting, and pagination support.
    """
    filters = {}

    # Build filters dynamically
    if field1:
        filters['field1'] = field1

    # Date range filters
    if date_from and date_to:
        filters['posting_date'] = ['between', [date_from, date_to]]

    # Get data using Frappe's database API
    results = frappe.db.get_all(
        'Your DocType',
        filters=filters,
        fields=['name', 'field1', 'field2', 'amount', 'status'],
        order_by=f'{sort_by} {sort_order}',
        limit=limit,
        start=offset
    )

    # Get total count for pagination
    total_count = frappe.db.count('Your DocType', filters=filters)

    # Calculate summary statistics (optional)
    summary = {}
    if results:
        total_amount = sum(r.get('amount', 0) for r in results)
        summary = {
            'total_records': len(results),
            'total_amount': total_amount,
            'average_amount': total_amount / len(results)
        }

    return json.dumps({
        'data': results,
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
        'summary': summary
    }, default=custom_json_serializer)
```

### 2. Define the Tool Schema

Add a tool definition dictionary following OpenAI's function calling schema:

```python
list_your_doctype_tool = {
    "type": "function",
    "function": {
        "name": "list_your_doctype",
        "description": "List and search documents with advanced filtering, sorting, and pagination",
        "parameters": {
            "type": "object",
            "properties": {
                # Filter properties
                "field1": {
                    "type": "string",
                    "description": "Filter by field1"
                },
                "status": {
                    "type": "string",
                    "enum": ["Draft", "Submitted", "Cancelled"],
                    "description": "Document status"
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)"
                },
                "date_to": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)"
                },

                # Sorting properties
                "sort_by": {
                    "type": "string",
                    "enum": ["creation", "modified", "name", "amount"],
                    "description": "Field to sort by"
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "description": "Sort order"
                },

                # Pagination properties
                "limit": {
                    "type": "integer",
                    "description": "Number of records to return (default: 10, max: 100)"
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of records to skip"
                }
            },
            "required": []  # Usually empty, as all parameters are optional
        }
    }
}
```

### 3. Register the Tool

Add your tool to the exports at the bottom of `tools.py`:

```python
# In the tools list
def get_tools():
    tools = [
        # ... existing tools ...
        list_your_doctype_tool,
    ]
    return tools

# In the available_functions dictionary
available_functions = {
    # ... existing functions ...
    "list_your_doctype": list_your_doctype,
}
```

### Best Practices for Tool Implementation

1. **Consistent Parameters**: Always include standard filter, sort, and pagination parameters for list functions
2. **Error Handling**: Wrap database queries in try-except blocks
3. **Data Serialization**: Use the `custom_json_serializer` for handling ERPNext data types (Decimal, datetime, etc.)
4. **Summary Statistics**: Include helpful aggregations (totals, averages, counts) in list responses
5. **Special Filters**:
   - For serial number searches, query the Serial and Batch Entry table first
   - For text searches, use SQL LIKE queries across relevant fields
   - For item-based filters, join with item tables as needed
6. **Performance**:
   - Set reasonable default limits (10-20 records)
   - Use indexed fields for filtering and sorting
   - Consider using Frappe Query Builder for complex queries
7. **Documentation**: Provide clear descriptions in the tool schema for the AI to understand when and how to use the tool

### Example: Complex Query with Joins

For more complex scenarios involving multiple tables:

```python
def get_invoice_with_items(invoice_name):
    """Get invoice details including all line items."""

    # Get main document
    invoice = frappe.db.get_value(
        'Sales Invoice',
        invoice_name,
        ['*'],
        as_dict=True
    )

    if not invoice:
        return json.dumps({'error': 'Invoice not found'})

    # Get child table items
    items = frappe.db.get_all(
        'Sales Invoice Item',
        filters={'parent': invoice_name},
        fields=['item_code', 'item_name', 'qty', 'rate', 'amount']
    )

    invoice['items'] = items

    return json.dumps(invoice, default=custom_json_serializer)
```