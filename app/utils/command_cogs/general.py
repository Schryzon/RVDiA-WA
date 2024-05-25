from os import getenv
from scripts import heading
from dotenv import load_dotenv
from PIL import Image
from time import time
import aiohttp
import os
import base64
from openai import AsyncOpenAI
from scripts import process_help_command
from quart import current_app
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIClient = AsyncOpenAI(
        api_key=OPENAI_API_KEY
)   

async def ping():
    """
    Menampilkan latency ke WhatsApp API
    """
    start_time = time()
    headers = {
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        await session.get(f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}")
        end_time = time()
        delta = end_time - start_time
    return f"Pong!\nLatency-ku ke WhatsApp adalah *{round(delta*100, 2)} ms*."

def greet():
    """
    Her first command!
    """
    return "Hello, command ini berhasil dijalankan!"

def repeat(*prompt):
    """
    Mengulangi apapun yang dikatakan.
    """
    full_prompt = ' '.join(prompt).strip()
    return full_prompt

def say(*prompt):
    """
    Alternatif dari command repeat
    """
    return repeat(*prompt)

async def cuaca(*location):
    """
    Lihat info tentang keadaan cuaca di suatu kota atau daerah!
    """
    full_location = ' '.join(location).strip()
    try:
        async with aiohttp.ClientSession() as session:
            # Need to decode geocode consisting of latitude and longitude
            data = await session.get(f'http://api.openweathermap.org/geo/1.0/direct?q={full_location}&limit=1&appid={getenv("openweatherkey")}')
            data = await data.json()
            geocode = [data[0]['lat'], data[0]['lon']]
            result = await session.get(f"https://api.openweathermap.org/data/2.5/weather?lat={geocode[0]}&lon={geocode[1]}&lang=id&units=metric&appid={getenv('openweatherkey')}")
            result = await result.json()
            #icon = f"http://openweathermap.org/img/wn/{result['weather'][0]['icon']}@4x.png"
            title=f"Cuaca di {result['name']}"
            description=f"_{result['weather'][0]['description'].title()}_\n"

            temp = result['main']
            suhu=f"Suhu ({temp['temp']}°C)"
            feels_like = f"*Terasa seperti:* {temp['feels_like']}°C\n*Minimum:* {temp['temp_min']}°C\n*Maksimum:* {temp['temp_max']}°C"
            atmo_press= f"*Tekanan Atmosfer:* {temp['pressure']} hPa\n*Kelembaban:* {temp['humidity']}%\n*Persentase Awan:* {result['clouds']['all']}%\n"

            wind = result['wind']
            angin = "Angin"
            attr_angin = f"*Kecepatan:* {wind['speed']} m/s\n*Arah:* {wind['deg']}° ({heading(wind['deg'])})"
            combined_strings = '\n'.join([title, description, suhu, feels_like, atmo_press, angin, attr_angin])
            # A reminder to not leave a single comma at the end of each variable declarations
            # I learned it the hard way, damn it
            return combined_strings

    except(IndexError):
        return "Maaf, aku tidak bisa menemukan lokasi itu!"
    
def crop_to_square(img_path):
    """
    Converts ANY aspect ratio to 1:1
    Thanks, RVDIA!
    """
    with Image.open(img_path) as img:
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = (width + size) // 2
        bottom = (height + size) // 2
        cropped = img.crop((left, top, right, bottom))
        cropped.save(img_path[2:])
        cropped.close()

async def generate(*prompt):
        """
        Ciptakan sebuah karya seni dua dimensi dengan perintah!
        """
        full_prompt = ' '.join(prompt).strip()
        start=time()
        result = await AIClient.images.generate(
            model='dall-e-2',
            prompt=full_prompt,
            size='1024x1024',
            response_format='b64_json',
            n=1
        )
        b64_data = result.data[0].b64_json; end=time() # Finished generating and gained data
        decoded_data = base64.b64decode(b64_data)
        with open('generated.png', 'wb') as image:
            image.write(decoded_data)
        required_time=end-start

        return [f'Prompt: *{full_prompt}*\nWaktu dibutuhkan: *{round(required_time, 2)} detik*', './generated.png']

async def variasi():
    crop_to_square(f'./saved_items/images/Image.jpg')

    with Image.open("./saved_items/images/Image.jpg") as image:
        image.save("Image.png")
    selected_image = "Image.png"

    with open(selected_image, 'rb') as f:
        start=time()
        result = await AIClient.images.create_variation(
            image = f,
            model='dall-e-2',
            size='1024x1024',
            response_format = 'b64_json',
            n=1
        )
        end=time()
    b64_data = result.data[0].b64_json
    decoded_data = base64.b64decode(b64_data)
    with open('variation.png', 'wb') as image_file:
        image_file.write(decoded_data)
    required_time=end-start

    return [f'Ini dia!\nWaktu dibutuhkan: *{round(required_time, 2)} detik*', './variation.png']

def help():
    """
    Memperlihatkan pesan ini
    """
    all_commands = '\n'.join(process_help_command())
    reply = f"*-- DAFTAR COMMAND RVDiA --*\n\n" + all_commands
    return reply