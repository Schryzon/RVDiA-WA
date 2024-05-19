import logging
from flask import current_app, jsonify
import json
import requests
from openai import OpenAI
import os
import threading
from .command import check_command, prefixes, execute_command
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# from app.services.openai_service import generate_response
import re



def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


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


def generate_response(response:str, user_name):
    """
    Generate a response to the user
    If a command prefix is detected, it runs a command
    Else, it will initiate a convo with the AI
    """
    command = check_command(response)
    if command:
        args = command[1][2]
        return execute_command(command[1][1], *command[1][2]) if args else execute_command(command[1][1])
        # return f"Command detected! {command[0], command[1][0], command[1][1], command[1][2]}"

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    AIClient = OpenAI(
        api_key=OPENAI_API_KEY
    )
    ROLE = os.getenv("rolesys")
    currentTime = datetime.now()
    date = currentTime.strftime("%d/%m/%Y")
    hour = currentTime.strftime("%H:%M:%S")
    result = AIClient.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=1.2,
        messages=[
        {"role":'system', 'content':ROLE + f" You are currently chatting with {user_name}."},
        {"role":'assistant', 'content':f"The current date is {date} at {hour} UTC+8"},
        {"role": "user", "content": response}
        ]
    )
    return result.choices[0].message.content


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response

"""
# Failed threading attempt
def send_message(data):
    def send_message_thread(data):
        with current_app.app_context():
            headers = {
                "Content-type": "application/json",
                "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
            }

            url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

            try:
                response = requests.post(
                    url, data=data, headers=headers, timeout=10
                )  # 10 seconds timeout as an example
                response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
            except requests.Timeout:
                logging.error("Timeout occurred while sending message")
                return jsonify({"status": "error", "message": "Request timed out"}), 408
            except (
                requests.RequestException
            ) as e:  # This will catch any general request exception
                logging.error(f"Request failed due to: {e}")
                return jsonify({"status": "error", "message": "Failed to send message"}), 500
            else:
                # Process the response as normal
                log_http_response(response)
                return response

    thread = threading.Thread(target=send_message_thread, args=(data,))
    thread.start()"""


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    # TODO: implement custom function here
    response = generate_response(message_body, name)

    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    #data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    data = get_text_message_input(wa_id, response)
    send_message(data)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
