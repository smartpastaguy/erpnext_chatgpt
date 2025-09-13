# Troubleshooting Guide

## "Client.init() got an unexpected keyword argument 'proxies'" Error

This error occurs when something tries to pass unsupported parameters to the OpenAI client. The OpenAI Python SDK v1.x doesn't accept a 'proxies' parameter.

### Solution Applied:
The code has been simplified to use only the required `api_key` parameter when initializing the OpenAI client. No proxy settings or extra parameters are needed.

### To deploy the fix:

1. **Update your code** with the simplified `api.py`
2. **Clear Frappe cache:**
   ```bash
   bench clear-cache
   bench restart
   ```

### Why this happens:
- Frappe v15 might be trying to pass HTTP client configurations that aren't compatible with OpenAI SDK v1.x
- The OpenAI SDK only needs the API key - it handles its own HTTP connections

## Other Common Issues

### Model Not Available
If you get errors about "gpt-4o-mini" not being available:
- The code now uses "gpt-3.5-turbo" by default (widely available)
- To use GPT-4, change the MODEL constant in `api.py`:
  ```python
  MODEL = "gpt-4"  # or "gpt-4-turbo"
  ```

### API Key Issues
1. Verify your API key in ERPNext:
   - Go to OpenAI Settings
   - Enter your API key
   - Save

2. Test directly in bench console:
   ```python
   bench console
   from openai import OpenAI
   client = OpenAI(api_key="your-key-here")
   list(client.models.list())
   ```

### Chat Button Not Appearing
- Ensure you're logged in as System Manager
- Check browser console for JavaScript errors
- Verify API key is set and valid

## What Was Removed
- Proxy handling code (not needed for typical deployments)
- Complex parameter filtering
- OpenAI wrapper module

The simpler approach is more maintainable and less prone to compatibility issues.