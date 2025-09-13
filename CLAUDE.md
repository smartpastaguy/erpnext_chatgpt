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