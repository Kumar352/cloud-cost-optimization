# Embed an AWS conversational assistant in the dashboard

## Why there are two AWS chat products here

- **Amazon Q Developer in the AWS Console** is the assistant shown in the user's screenshot. It is useful for AWS design, service guidance, account insights, and debugging from the console, but its console chat panel is not a public chat endpoint that the Streamlit app can directly call.
- **Amazon Quick custom chat agents** support embedding in an external application after the hosting URL is allow-listed. This is the supported AWS-native embedding path for the Streamlit UI.

Official guide: https://docs.aws.amazon.com/quick/latest/userguide/custom-agents.html

## Configure Amazon Quick once

1. Open the Amazon Quick console in US East (N. Virginia): https://us-east-1.quicksight.aws.amazon.com/sn/start
2. Open **Chat agents** → **Create chat agent**. Create a general-purpose agent and give it a helpful, concise technical-assistant personality. Test it and select **Launch chat agent**.
3. For the agent, choose **Share** → **Share via embed**. Copy the `src` URL from the generated iframe code. Do not paste the entire iframe markup into the environment variable.
4. In the Amazon Quick account's **Manage account → Security → Manage domains** settings, add the local app origin `http://localhost:8503`. If Quick requires HTTPS or rejects localhost in your account, use an approved HTTPS development host instead.
5. In the same PowerShell terminal used to launch Streamlit, set the embed URL and start the application:

~~~powershell
Set-Location "$env:USERPROFILEOneDriveDesktopBigDatacloud-cost-optimization"

$env:CLOUD_COST_QUICK_EMBED_URL = "PASTE_THE_GENERATED_IFRAME_SRC_URL_HERE"
python -m streamlit run src/dashboard.py --server.port 8503
~~~

The dashboard verifies that the value is an HTTPS Amazon Quick/QuickSight embed endpoint before rendering the iframe. It does not create AWS resources.

## Connect the agent to project knowledge

A general-purpose agent can answer general questions from model knowledge. To answer questions from project documents or CUR data, set up and grant it access to a suitable Amazon Quick knowledge source/space containing the intended files or curated data. The iframe does not automatically transfer the dashboard's in-memory CUR DataFrame into Quick. Do not assume it can see current costs until the relevant data source is configured and tested.

## Performance and troubleshooting

- The embedded chat runs in its own frame, so a slow inference request should not freeze the surrounding Streamlit charts.
- If the embed is blank or shows a permission error, verify the URL is the `src` value from **Share via embed**, the host origin is allow-listed, and the browser is signed in to Amazon Quick.
- Amazon Quick access/subscription and use of connected services may incur costs. Confirm the account's current service access and pricing before using it for a demonstration.
- The optional Bedrock fallback streams generated text, sets short network timeouts, and disables retries beyond the initial request. If it returns `ValidationException: Operation not allowed`, this is an AWS model/account inference restriction rather than a dashboard layout issue. The application does not hide the error or make up an answer.
