import frappe
from frappe import _
from openai import OpenAI
import json
from typing import List, Dict, Any
from erpnext_chatgpt.erpnext_chatgpt.tools import get_tools, available_functions

def get_pre_prompt():
    """Get the pre-prompt with current date."""
    return f"You are an AI assistant integrated with ERPNext. Please provide accurate and helpful responses based on the following questions and data provided by the user. The current date is {frappe.utils.now()}."

def get_model_settings():
    """Get model and max_tokens from settings."""
    model = frappe.db.get_single_value("OpenAI Settings", "model")
    max_tokens = frappe.db.get_single_value("OpenAI Settings", "max_tokens")

    # Use defaults if not set
    if not model:
        model = "gpt-3.5-turbo"
    if not max_tokens:
        max_tokens = 8000

    return model, max_tokens

def get_openai_client() -> OpenAI:
    """Get the OpenAI client with the API key from settings."""
    api_key = frappe.db.get_single_value("OpenAI Settings", "api_key")
    if not api_key:
        frappe.throw(_("OpenAI API key is not set in OpenAI Settings."))

    # Simple, clean initialization - OpenAI SDK v1.x only needs api_key
    # No proxies, no complex parameters
    return OpenAI(api_key=api_key)

def handle_tool_calls(tool_calls: List[Any], conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Handle the tool calls by executing the corresponding functions and appending the results to the conversation."""
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = available_functions.get(function_name)
        if not function_to_call:
            frappe.log_error(f"Function {function_name} not found.", "OpenAI Tool Error")
            raise ValueError(f"Function {function_name} not found.")

        function_args = json.loads(tool_call.function.arguments)
        try:
            function_response = function_to_call(**function_args)
        except Exception as e:
            frappe.log_error(f"Error calling function {function_name} with args {json.dumps(function_args)}: {str(e)}", "OpenAI Tool Error")
            raise

        conversation.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": str(function_response),
        })
    return conversation

def estimate_token_count(messages: List[Dict[str, Any]]) -> int:
    """
    Estimate the token count for a list of messages.
    This is a rough estimation; OpenAI provides more accurate token counting in their own libraries.
    """
    tokens_per_message = 4  # Average tokens per message (considering metadata)
    tokens_per_word = 1.5   # Average tokens per word (this may vary)

    return sum(tokens_per_message + int(len(str(message.get("content", "")).split()) * tokens_per_word)
               for message in messages if message.get("content") is not None)

def trim_conversation_to_token_limit(conversation: List[Dict[str, Any]], token_limit: int = None) -> List[Dict[str, Any]]:
    """
    Trim the conversation so that its total token count does not exceed the specified limit.
    Keeps the most recent messages and trims older ones.
    """
    if token_limit is None:
        _, token_limit = get_model_settings()
    while estimate_token_count(conversation) > token_limit and len(conversation) > 1:
        # Remove the oldest non-system message
        for i, message in enumerate(conversation):
            if message.get("role") != "system":
                del conversation[i]
                break
    return conversation

@frappe.whitelist()
def ask_openai_question(conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ask a question to the OpenAI model and handle the response.

    :param conversation: List of conversation messages.
    :return: The response from OpenAI or an error message.
    """
    try:
        client = get_openai_client()

        # Add the pre-prompt as the initial message if not present
        if not conversation or conversation[0].get("role") != "system":
            conversation.insert(0, {"role": "system", "content": get_pre_prompt()})

        # Get model settings
        model, max_tokens = get_model_settings()

        # Trim conversation to stay within the token limit
        conversation = trim_conversation_to_token_limit(conversation, max_tokens)

        frappe.logger("OpenAI").debug(f"Conversation: {json.dumps(conversation)}")

        tools = get_tools()
        response = client.chat.completions.create(
            model=model,
            messages=conversation,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        frappe.logger("OpenAI").debug(f"OpenAI Response: {response_message}")

        tool_calls = response_message.tool_calls
        if tool_calls:
            conversation.append(response_message.model_dump())
            conversation = handle_tool_calls(tool_calls, conversation)

            # Trim again if needed after tool calls
            conversation = trim_conversation_to_token_limit(conversation, max_tokens)

            second_response = client.chat.completions.create(
                model=model,
                messages=conversation
            )
            return second_response.choices[0].message.model_dump()

        return response_message.model_dump()
    except Exception as e:
        frappe.log_error(str(e), "OpenAI API Error")
        return {"error": str(e)}

@frappe.whitelist()
def test_openai_api_key(api_key: str) -> bool:
    """
    Test if the provided OpenAI API key is valid.

    :param api_key: The OpenAI API key to test.
    :return: True if the API key is valid, False otherwise.
    """
    try:
        # Simple client creation with just the API key
        client = OpenAI(api_key=api_key)
        # Test the key by listing models
        list(client.models.list())
        return True
    except Exception as e:
        frappe.log_error(str(e), "OpenAI API Key Test Failed")
        return False

@frappe.whitelist()
def get_available_models() -> List[str]:
    """
    Get list of available OpenAI models for the current API key.

    :return: List of model IDs that can be used for chat completions
    """
    try:
        client = get_openai_client()
        models = list(client.models.list())

        # Filter for chat models
        chat_models = []
        for model in models:
            if any(prefix in model.id for prefix in ["gpt-3.5", "gpt-4"]):
                chat_models.append(model.id)

        # Sort models for better display
        chat_models.sort()
        return chat_models
    except Exception as e:
        frappe.log_error(str(e), "Failed to fetch available models")
        # Return default models if API call fails
        return ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"]

@frappe.whitelist()
def test_connection() -> Dict[str, Any]:
    """
    Test the OpenAI connection by initializing the client and making a simple API call.

    :return: Dictionary with success status and message.
    """
    try:
        # Get the API key from settings
        api_key = frappe.db.get_single_value("OpenAI Settings", "api_key")
        if not api_key:
            return {"success": False, "message": _("OpenAI API key is not set. Please enter an API key first.")}

        # Initialize the OpenAI client
        client = OpenAI(api_key=api_key)

        # Test the connection by listing models
        models = list(client.models.list())

        if models:
            return {"success": True, "message": _("Connection successful! OpenAI API is working correctly.")}
        else:
            return {"success": False, "message": _("Connection established but no models available.")}

    except Exception as e:
        frappe.log_error(str(e), "OpenAI Connection Test Failed")
        return {"success": False, "message": _("Connection failed: {0}").format(str(e))}

@frappe.whitelist()
def check_openai_key_and_role() -> Dict[str, Any]:
    """
    Always show the chat button for all users.

    :return: Dictionary indicating to always show the button.
    """
    return {"show_button": True}