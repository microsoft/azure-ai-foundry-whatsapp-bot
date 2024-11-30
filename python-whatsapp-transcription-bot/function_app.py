import azure.functions as func
import logging
import os
import json
import requests
from openai import AzureOpenAI

app = func.FunctionApp()

@app.route(route="WhatsAppTranscriptionBot", auth_level=func.AuthLevel.ANONYMOUS)
def WhatsAppTranscriptionBot(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request')

    logging.info(f"req.method: {req.method}")

    if req.method == 'POST':
        return(handle_message(req))
    else:
        return(verify(req))
        

def verify(req):
    logging.info("verify - Start")

    verify_token = os.environ["VERIFY_TOKEN"]
    if verify_token:
        logging.info(f"verify_token: {verify_token}")
    else:
        logging.info("VERIFY_TOKEN Empty")

    if req.params:
        logging.info(req.params)

    # Parse params from the webhook verification request
    mode = req.params.get("hub.mode")
    token = req.params.get("hub.verify_token")
    challenge = req.params.get("hub.challenge")
    logging.info(f"mode: {mode}, token: {token}, challenge: {challenge}")

    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == verify_token:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return func.HttpResponse(
                challenge,
                status_code=200
            )
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return func.HttpResponse(
                "Verification failed",
                status_code=403
            )
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return func.HttpResponse(
            "Missing parameters",
            status_code=400
        )


def handle_message(req):
    logging.info("handle_message - Start")

    body = req.get_json()
    logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return func.HttpResponse(
                "OK",
                status_code=200
                )

    try:
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return func.HttpResponse(
                "OK",
                status_code=200
                )
        else:
            # if the request is not a WhatsApp API event, return an error
            logging.error("Not a WhatsApp API event")
            return func.HttpResponse(
                "Not a WhatsApp API event",
                status_code=404
                )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return func.HttpResponse(
                "Invalid JSON provided",
                status_code=400
                )


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    logging.info("is_valid_whatsapp_message - Start")
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )


def process_whatsapp_message(body):
    logging.info("process_whatsapp_message - Start")

    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    logging.info(f"wa_id: {wa_id}")
    logging.info(f"name: {name}")

    # Safeguard against unauthorized users
    if wa_id != os.environ["RECIPIENT_WAID"]:
        logging.error("Unauthorized user!!!")
        return

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    logging.info(f"message: {message}")

    if "text" in message:
        logging.info(f"Message Type: TEXT")
        message_body = message["text"]["body"]
        logging.info(f"message_body: {message_body}")
        text = "Hi, I am Dave the Bot. I can help you transcribe WhatsApp voice messages using AI. Just forward me the message" 
        data = get_text_message_input(wa_id, text)
        send_message(data)
    elif "audio" in message:
        logging.info(f"Message Type: AUDIO")
        media_id = message["audio"]["id"]
        logging.info(f"media_id: {media_id}")
        text = "Transcribing the message. Will return shortly with the transacription"
        data = get_text_message_input(wa_id, text)
        send_message(data)
        handle_voice_message(media_id)
    else:
        logging.error(f"Unknown Message Type")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def send_message(data):
    logging.info("send_message - Start")

    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{os.environ['VERSION']}/{os.environ['PHONE_NUMBER_ID']}/messages"
    return(send_post_request_to_graph_facebook(url, data, headers))
    

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def send_post_request_to_graph_facebook(url, data, headers):
    logging.info(f"send_post_request_to_graph_facebook - Strat, url: {url}, data: {data}, data type: {type(data)}")

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return func.HttpResponse(
                "Request timed out",
                status_code=408
                )
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return func.HttpResponse(
                "Failed to send message",
                status_code=500
                )
    else:
        # Process the response as normal
        log_http_response(response)
        return(response)
    

def send_get_request_to_graph_facebook(url, headers):
    logging.info(f"send_get_request_to_graph_facebook - Strat, URL: {url}")

    try:
        response = requests.get(
            url, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return func.HttpResponse(
                "Request timed out",
                status_code=408
                )
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return func.HttpResponse(
                "Failed to send message",
                status_code=500
                )
    else:
        # Process the response as normal
        log_http_response(response)
        return(response)


def handle_voice_message(media_id):
    logging.info("handle_voice_message - Start")

    ## Retrieve Media URL
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{os.environ['VERSION']}/{media_id}"
    response = send_get_request_to_graph_facebook(url, headers)

    response_json = json.loads(response.text)
    logging.info(f"response_json - {response_json}")
    download_url = response_json["url"]
    logging.info(f"download_url - {download_url}")

    ## Download Media
    url = f"{download_url}"
    response = send_get_request_to_graph_facebook(url, headers)

    local_file_name = '/tmp/voice_message.ogg'
    data = requests.get(url, headers=headers, allow_redirects=True)

    # Save file data to local copy
    with open(local_file_name, 'wb') as file:
        file.write(data.content)

    logging.info(f"File saved - {local_file_name}")
    transcribed_text = transcribe_file(local_file_name)
    if transcribed_text:
        data = get_text_message_input(os.environ["RECIPIENT_WAID"], "*Transcribed by AI*\n" + transcribed_text)
        send_message(data)
    

def transcribe_file(audio_file):
    logging.info(f"audio_file - Start, file: {audio_file}")
    
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version="2024-02-01",
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    deployment_id = "whisper" #This will correspond to the custom name you chose for your deployment when you deployed a model."

    transcribed_text = client.audio.transcriptions.create(
        file=open(audio_file, "rb"),            
        model=deployment_id,
        response_format="text"
    )

    logging.info(f"transcribed_text - {transcribed_text}")
    return(transcribed_text)
