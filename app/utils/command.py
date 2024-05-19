"""
File for handling message-based commands
Pretty much a nostalgia to Discord's!
"""
import requests
from os import getenv
from .scripts import heading
from dotenv import load_dotenv
load_dotenv()

prefixes = [
    "rvd ",
    "r!",
    "!"
]

def check_command(message_body:str):
    """
    Check if the message contains a command.
    """
    for prefix in prefixes:
        if message_body.startswith(prefix):
            message_without_prefix = message_body[len(prefix):].strip()
            # Split the message into parts
            parts = message_without_prefix.split()
            if len(parts) > 0:
                command_name = parts[0]
                args = parts[1:] or None
                return [True, (prefix, command_name, args)]
    return False

def execute_command(command_name:str, *args):
    """
    Execute commands, pretty much like eval()
    Though, this one accepts variable args!
    """
    func = globals().get(command_name.lower()) # Trying to make it case insensitive
    if func and callable(func):
        try:
            return func(*args)
        except Exception as e:
            return e
    else:
        return f"No command called {command_name} found."
    
"""
Collection of commands
Currently unorganized, maybe gonna attempt to do one
"""
    
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

def weather(*location):
    """
    Lihat info tentang keadaan cuaca di suatu kota atau daerah!
    """
    full_location = ' '.join(location).strip()
    try:
        # Need to decode geocode consisting of latitude and longitude
        data = requests.get(f'http://api.openweathermap.org/geo/1.0/direct?q={full_location}&limit=1&appid={getenv("openweatherkey")}')
        data = data.json()
        geocode = [data[0]['lat'], data[0]['lon']]
        result = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={geocode[0]}&lon={geocode[1]}&lang=id&units=metric&appid={getenv('openweatherkey')}")
        result = result.json()
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