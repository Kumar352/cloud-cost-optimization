# Configure the AWS chatbot for Cloud Cost Copilot

## Important distinction

The Amazon Q Developer panel in the AWS Management Console (the pane that says “How can I help you today?”) is a console assistant. It is not an embeddable iframe endpoint or a public chat API that a Streamlit app can call directly.

For an AWS-native assistant embedded in the dashboard, use **Amazon Q Business embedded web experience**. AWS documents embedding the deployed web experience in an iframe:
https://docs.aws.amazon.com/amazonq/latest/qbusiness-ug/embed-web-experience.html

## Current account status

The last AWS account inventory found **zero Amazon Q Business applications**. Therefore, no real Q Business chat endpoint is currently available to embed. The dashboard shows setup instructions instead of a red URL validation error. The account's Amazon Nova Lite availability check also returned `authorizationStatus=NOT_AUTHORIZED`, so direct Bedrock chat must not be expected to answer until model access is fixed.

## Option A — Embed Amazon Q Business

1. Open the [Amazon Q Business console](https://console.aws.amazon.com/amazonq/home) in the required region.
2. Create an Amazon Q Business application and complete the required identity configuration and web experience setup. This is a new AWS service configuration and may have charges; review pricing before proceeding.
3. If you want it to answer from project documents or billing data, add a suitable, permissioned knowledge source and wait for ingestion to complete. The iframe does not automatically read the data held in Streamlit memory.
4. Under the application's **Amazon Q embedded** or web-experience settings, add the dashboard's base URL `http://localhost:8503` to allowed origins if your configuration supports localhost; use an approved HTTPS development origin if required.
5. Copy the **Deployed URL/defaultEndpoint** for the web experience. Use that URL, not the AWS Console Home URL and not an arbitrary Chat agents listing URL.
6. In the PowerShell terminal that starts Streamlit, set the variable and start the dashboard:

~~~powershell
Set-Location "$env:USERPROFILEOneDriveDesktopBigDatacloud-cost-optimization"
$env:CLOUD_COST_QBUSINESS_EMBED_URL = "PASTE_THE_DEPLOYED_Q_BUSINESS_WEB_EXPERIENCE_URL_HERE"
python -m streamlit run src/dashboard.py --server.port 8503
~~~

The shared Copilot section is displayed in both Live AWS billing and Synthetic cross-cloud demo modes. The same embed URL is used regardless of the selected dashboard data mode.

## Option B — Enable the Bedrock chat fallback

The shared widget includes a streaming Bedrock chat form in both data modes. The AWS inventory currently shows the selected Nova Lite model as `NOT_AUTHORIZED` for this account. In the AWS Console:

1. Open [Amazon Bedrock model access in us-east-1](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess).
2. Enable/request access for **Amazon Nova Lite** following the current console workflow and confirm that access shows as granted/available.
3. Ensure the identity launching Streamlit has the required `bedrock:InvokeModel` permissions (streaming calls may also require `bedrock:InvokeModelWithResponseStream`).
4. Retry a short prompt from the dashboard.

Model inference is pay-per-use and can incur charges. If the error still says `Operation not allowed`, check account policy/permissions and the model's authorization status; do not keep retrying the same request.

## Why the chatbot is present in both dashboard modes

The chat UI is rendered outside the source-specific analytics branches. In Live AWS mode, its context includes compact, currency-specific aggregates from the loaded CUR. In Synthetic demo mode, its context is explicitly marked as illustrative demo data. The same chat history and composer are used; switching data mode does not remove the chat widget.
