# Azure AI Foundry Whatsapp Bot

## Overview 
This GitHub repository walk you through creating a WhatsApp Bot built with Azure Functions and Azure AI Foundry, using Python.

## Architecture

![Architecture](img/architecture.png)

 - A user gets a voice message. He/She then forwards the message to the WhatsApp Business number. 
 - WhatsApp Business app gets the message and sends it to the Azure Functions using a Webhook.
 - Azure Functions gets the message. If is is a voice messsage, then call `client.audio.transcriptions.create` Python API to invoke Azure OpenAI Whsiper model, deployed in Azure AI Foundry.
 - Transcribed text is returned from Azure OpenAI Whsiper model to Azure Function, and from the to the WhatsApp Business app.

## Prerequisites

 - Azure Subscription with permissions to create the following Azure resources: Resource Groups, Storage Accounts, Function Apps, and AI Foundry (formerly named AI Studio).
 - A Meta for Developers account — If you don’t have one, you can create a Meta for Developers account [here](https://developers.facebook.com/).
 - Basic Python knowledge is required to follow this tutorial.


## Instructions
- Quickstart: Create a Python function in Azure from the command line - refer to [Documentation](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python)

