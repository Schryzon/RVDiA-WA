import logging
from quart import current_app, jsonify
import json
import requests
from openai import OpenAI, AsyncOpenAI
import os
import threading
from .command import check_command, prefixes, execute_command
from datetime import datetime
from dotenv import load_dotenv
from .command import check_command, prefixes, execute_command
import aiohttp
import asyncio
load_dotenv()

# from app.services.openai_service import generate_response
import re

"""
#UbahKeAsync
"""


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


async def generate_response(response, user_name):
    """
    Generate a response to the user
    If a command prefix is detected, it runs a command
    Else, it will initiate a convo with the AI
    """
    command = check_command(response)
    if command:
        args = command[1][2]
        return await execute_command(command[1][1], *command[1][2]) if args else execute_command(command[1][1])
        # return f"Command detected! {command[0], command[1][0], command[1][1], command[1][2]}"

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    AIClient = AsyncOpenAI(
        api_key=OPENAI_API_KEY
    )
    ROLE = os.getenv("rolesys")
    currentTime = datetime.now()
    date = currentTime.strftime("%d/%m/%Y")
    hour = currentTime.strftime("%H:%M:%S")
    result = await AIClient.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=1.2,
        messages=[
        {"role":'system', 'content':ROLE + f" You are currently chatting with {user_name}."},
        {"role":'assistant', 'content':f"The current date is {date} at {hour} UTC+8"},
        {"role": "user", "content": response}
        ]
    )
    return result.choices[0].message.content


async def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    async with aiohttp.ClientSession() as session:
        url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
        try:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    print("Status:", response.status)
                    print("Content-type:", response.headers["content-type"])

                    html = await response.text()
                    print("Body:", html)
                else:
                    print(response.status)
                    print(response)
        except aiohttp.ClientConnectorError as e:
            print("Connection Error", str(e))


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


async def process_whatsapp_message(body):
    print(body)
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    # TODO: implement custom function here
    response = await generate_response(message_body, name)

    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    #data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    data = get_text_message_input(wa_id, response)
    return await send_message(data)


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