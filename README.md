# Azure AI Foundry Whatsapp Bot
WhatsApp Bot built with Azure Functions and Azure AI Foundry, using Python.

# Architecture

![Architecture](img/architecture.png)

1. A user gets a voice message. He/She then forwards the message to the WhatsApp Business number. 
2. WhatsApp Business app gets the message and sends it to the Azure Functions using Webhook.
3. Azure Functions gets the message. If is is a voice messsage, then call `client.audio.transcriptions.create` Python API to invoke Azure OpenAI Whsiper model, deployed in Azure AI Foundry.
4. Transcribed text is returned from Azure OpenAI Whsiper model to Azure Function, and from the to the WhatsApp Business app.

# Instructions
- Quickstart: Create a Python function in Azure from the command line - refer to [Documentation](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python)

