frappe.ui.form.on("OpenAI Settings", {
  refresh: function (frm) {
    // Add custom button to test API key
    frm.add_custom_button(__("Test Connection"), function () {
      frappe.call({
        method: "erpnext_chatgpt.erpnext_chatgpt.api.test_connection",
        callback: function (r) {
          if (r.message) {
            if (r.message.success) {
              frappe.msgprint({
                title: __("Success"),
                message: r.message.message,
                indicator: "green",
              });
            } else {
              frappe.msgprint({
                title: __("Connection Failed"),
                message: r.message.message,
                indicator: "red",
              });
            }
          }
        },
        error: function(r) {
          frappe.msgprint({
            title: __("Error"),
            message: __("An error occurred while testing the connection."),
            indicator: "red",
          });
        }
      });
    });

    // Add help text for model selection
    if (frm.fields_dict.model) {
      frm.set_df_property("model", "description",
        "<b>Model Guide:</b><br>" +
        "• <b>gpt-3.5-turbo</b>: Fast, cost-effective, good for most tasks<br>" +
        "• <b>gpt-3.5-turbo-16k</b>: Same as above but with larger context window<br>" +
        "• <b>gpt-4</b>: Most capable, best for complex reasoning<br>" +
        "• <b>gpt-4-turbo</b>: Latest GPT-4 with vision capabilities<br>" +
        "• <b>gpt-4o</b>: Optimized GPT-4, faster responses<br>" +
        "• <b>gpt-4o-mini</b>: Smaller, faster version of GPT-4o<br>" +
        "<br><i>Note: GPT-4 models require API access. Check your OpenAI account for availability.</i>"
      );
    }

    // Add help text for max tokens
    if (frm.fields_dict.max_tokens) {
      frm.set_df_property("max_tokens", "description",
        "Maximum tokens for conversation context. Higher values allow longer conversations but may increase costs. " +
        "Recommended: 4000-8000 for normal use, 16000+ for long conversations."
      );
    }
  },

  api_key: function(frm) {
    // Mask the API key for security
    if (frm.doc.api_key && frm.doc.api_key.length > 10) {
      // Show only first 7 and last 4 characters
      let masked = frm.doc.api_key.substring(0, 7) + "..." + frm.doc.api_key.slice(-4);
      frm.set_df_property("api_key", "description", `Current key: ${masked}`);
    }
  },

  model: function(frm) {
    // Show cost indication when model changes
    const costInfo = {
      "gpt-3.5-turbo": "Low cost",
      "gpt-3.5-turbo-16k": "Low cost, larger context",
      "gpt-4": "Higher cost, best quality",
      "gpt-4-turbo": "Higher cost, latest features",
      "gpt-4o": "Moderate cost, optimized",
      "gpt-4o-mini": "Lower cost GPT-4"
    };

    if (frm.doc.model && costInfo[frm.doc.model]) {
      frappe.show_alert({
        message: `Model: ${frm.doc.model} (${costInfo[frm.doc.model]})`,
        indicator: "blue"
      }, 3);
    }
  }
});
