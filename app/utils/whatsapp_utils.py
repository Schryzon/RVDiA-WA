import logging
from quart import current_app, jsonify
import json
import openai
from openai import AsyncOpenAI
import os
from datetime import datetime
from dotenv import load_dotenv
from .command_handler import check_command, prefixes, execute_command
import aiohttp
from .scripts import upload_media
from contextlib import suppress
import mimetypes
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIClient = AsyncOpenAI(
        api_key=OPENAI_API_KEY
    )
# from app.services.openai_service import generate_response
import re

"""
#UbahKeAsync
"""


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_message_input(recipient, text, type, image_id = None, command_name = None):
    if type == "text" and not command_name == 'generate':
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            }
        )
    
    else:
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "IMAGE",
                "image": {"id": image_id, "caption":text},
            }
        )


async def generate_response(response, user_name, image_path):
    """
    Generate a response to the user
    If a command prefix is detected, it runs a command
    Else, it will initiate a convo with the AI
    """
    if response is None and image_path:
        return "Itu gambar apa yah?\nMohon maaf, aku masih belum bisa menganalisis foto secara langsung! >_<"
    command = check_command(response)
    if command:
        args = command[1][2]
        try:
            return await execute_command(command[1][1], *command[1][2]) if args else await execute_command(command[1][1])
        except Exception as e:
            return f"Wow! Command ini mengalami error!\nDetail error: {e}\nTolong laporkan ke Jayananda segera, ya!"
        # return f"Command detected! {command[0], command[1][0], command[1][1], command[1][2]}"

    ROLE = os.getenv("rolesys")
    currentTime = datetime.now()
    date = currentTime.strftime("%d/%m/%Y")
    hour = currentTime.strftime("%H:%M:%S")
    try:
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
    
    except openai.RateLimitError:
        return f"Waaaaah! Otakku sedang kepanasan!\nTolong berikan aku waktu istirahat sejenak, ya!"
    except openai.APITimeoutError:
        return f"Hmmm...\nKoneksiku ke server sedang ada kendala. Coba hubungi Jayananda, ya!"
    except openai.APIConnectionError:
        return f"E-ehh... uhm... sepertinya ada kendala saat aku menghubungkan diri ke server."
    except openai.InternalServerError:
        return f"Mohon maaf, fungsi untuk membalas chatmu sedang dalam gangguan.\nCoba lagi nanti, ya!"


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
                    logging.info(f"Status: {response.status}")
                    logging.info(f"Content-type: {response.headers['content-type']}")

                    html = await response.text()
                    logging.info(f"Body: {html}")
                else:
                    logging.warning(response.status)
                    logging.warning(response)
        except aiohttp.ClientConnectorError as e:
            logging.warning(f"Connection Error: {e}")


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
    """
    Process obtained message object to be read by RV
    """

    """
    Body Format Example

    {
    "object": "whatsapp_business_account",
    "entry": [
        {
        "id": "XXXX",
        "changes": [
            {
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {
                "display_phone_number": "XXXXXXX",
                "phone_number_id": "XXXXXXX"
                },
                "contacts": [
                {
                    "profile": {
                    "name": "XXXX"
                    },
                    "wa_id": "XXXX"
                }
                ],
                "messages": [
                {
                    "from": "XXXX",
                    "id": "XXXXXX",
                    "timestamp": "XXXXXXXXXX",
                    "type": "image",
                    "image": {
                    "caption": "XXXXXXXXXXXXX",
                    "mime_type": "image/jpeg",
                    "sha256": "XXXXXX",
                    "id": "XXXXXX"
                    }
                }
                ]
            },
            "field": "messages"
            }
        ]
        }
    ]
}
    """

    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_type = message["type"]

    # Different message processing based on type
    match message_type:
        case "text":
            message_body = message["text"]["body"]
            image_path = False

        case "image":
            headers = {
                "Content-type": "application/json",
                "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
            }

            # Get media URL
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{message['image']['id']}/"
                response = await session.get(url)
                response_json = await response.json()

            image_url = response_json['url']
            headers_2 = {
                "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
                "User-Agent": "curl/7.64.1"
            }

            # Download media from URL (hardest part)
            async with aiohttp.ClientSession(headers=headers_2) as session:
                data = await session.request(method="GET", url=image_url, ssl=False)
                print(f"Obtained data: {data}")
                content_type = data.headers.get('Content-Type')
                if content_type:
                    ext = mimetypes.guess_extension(content_type.split(';')[0])
                    if ext is None:
                        logging.warning("Could not determine file extension, defaulting to .jpg")
                        ext = ".jpg"
                else:
                    logging.warning("No Content-Type header found, defaulting to .jpg")
                    ext = ".jpg"

                image_path = os.path.join('./saved_items/images', f"Image{ext}")
                with open(image_path, "wb") as file:
                    file.write(await data.read())
                logging.warning(f"Saved an image to {image_path}")

            try:
                if message['image']['caption']:
                    message_body = message['image']['caption'] or None
            except:
                message_body = None

    # Create a response accordingly!
    response = await generate_response(message_body, name, image_path)

    with suppress(): # Doesn't seem to work, I used try-except blocks instead
        command = check_command(message_body)
        try:
            command_name = command[1][1]
            if message_type == 'image' or command_name == 'generate':
                print(f"Response: {response}")
                media_data = await upload_media(response[1])
                data = get_message_input(wa_id, response[0], message_type, image_id=media_data, command_name=command_name)
                os.remove(response[1])
            else:    
                data = get_message_input(wa_id, response, message_type)
        except:
            data = get_message_input(wa_id, response, message_type)

    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    #data = get_message_input(current_app.config["RECIPIENT_WAID"], response)
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