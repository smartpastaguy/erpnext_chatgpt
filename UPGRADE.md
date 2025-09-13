# Upgrade Guide

## Recent Changes

### Model Configuration (New Feature)
The OpenAI model is now configurable through the settings interface instead of being hardcoded.

### What Changed:
1. **OpenAI Settings DocType** now includes:
   - `model` field: Select which OpenAI model to use
   - `max_tokens` field: Configure maximum conversation context

2. **API Changes**:
   - Removed hardcoded `MODEL` and `MAX_TOKENS` constants
   - Model and token limits now read from database settings
   - Simplified OpenAI client initialization (removed proxy handling)

3. **Bug Fixes**:
   - Fixed "Client.init() got an unexpected keyword argument 'proxies'" error
   - Changed default model from "gpt-4o-mini" to "gpt-3.5-turbo" for wider availability

## Upgrade Steps

### For Existing Installations:

1. **Update the code**:
   ```bash
   cd apps/erpnext_chatgpt
   git pull
   ```

2. **Run migrations to update the DocType**:
   ```bash
   bench --site [your-site] migrate
   ```

3. **Clear cache and restart**:
   ```bash
   bench clear-cache
   bench restart
   ```

4. **Configure the new settings**:
   - Go to OpenAI Settings in ERPNext
   - Select your preferred model (default: gpt-3.5-turbo)
   - Optionally adjust Max Tokens (default: 8000)
   - Click "Test Connection" to verify everything works

### Breaking Changes:
- None. The system will use default values if settings are not configured.

### Notes:
- If you were using GPT-4 models before, you'll need to manually select them in settings
- The default model is now gpt-3.5-turbo for better compatibility
- Custom proxy configurations are no longer supported (use environment variables if needed)