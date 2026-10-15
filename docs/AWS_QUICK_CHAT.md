# Chatbot integration note

This older guide described Amazon Quick custom chat agents and is retained only to avoid a broken repository link.

The dashboard now uses one shared Cloud Cost Copilot widget across both data-source modes. For the supported Amazon Q embedded web experience, follow [AWS_Q_BUSINESS_CHAT.md](AWS_Q_BUSINESS_CHAT.md). Do not set the old CLOUD_COST_QUICK_EMBED_URL environment variable.

Amazon Q Developer inside AWS Console is not directly embeddable as a Streamlit iframe. The AWS account inventory found no Amazon Q Business application at the last check, so create a Q Business application and deployed web experience before setting CLOUD_COST_QBUSINESS_EMBED_URL.
