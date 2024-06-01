import aiohttp
import re
import aiofiles
from os import getenv
from io import BytesIO
import scripts

async def cuaca(*lokasi):
    """
    Lihat info tentang keadaan cuaca di suatu kota atau daerah!
    """
    full_location = ' '.join(lokasi).strip()
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
            attr_angin = f"*Kecepatan:* {wind['speed']} m/s\n*Arah:* {wind['deg']}° ({scripts.heading(wind['deg'])})"
            combined_strings = '\n'.join([title, description, suhu, feels_like, atmo_press, angin, attr_angin])
            # A reminder to not leave a single comma at the end of each variable declarations
            # I learned it the hard way, damn it
            return combined_strings

    except(IndexError):
        return "Maaf, aku tidak bisa menemukan lokasi itu!"
    
async def hex(*hex):
    """Memperlihatkan warna dari bilangan heksadesimal."""
    hex_value = ''.join(hex)
    if "#" in hex:
        hex_value = hex_value.split('#')[1]

    async def validate_hex(hex_str:str):
        pattern = r'^[0-9A-Fa-f]+$'  # Regular expression pattern for hexadecimal string
        if not re.match(pattern, hex_str):
            raise ValueError("Invalid hex!")
        
    try:
        await validate_hex(hex_value)
    except: # Malas
        return ["Hmm... sepertinya itu bukan bilangan heksadesimal yang valid!", './saved_items/images/qmark.png']
    
    hex_code = int(hex_value, 16)
    red = (hex_code >> 16) & 0xff # Bitwise right shift
    green = (hex_code >> 8) & 0xff
    blue = hex_code & 0xff
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://singlecolorimage.com/get/{hex_value}/500x500') as data:
            if data.status == 200:
                image_data = await data.read()
                file_path = f'./saved_items/generation/{hex_value.upper()}.png'
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(image_data)
            return [f"Hex: #{hex_value.upper()}\nRGB: ({red}, {green}, {blue})", file_path]


async def rgb(*rgb_value):
    """Memperlihatkan warna dari nilai RGB."""
    try:
        rgb_values = [int(rgb_value[0]), int(rgb_value[1]), int(rgb_value[2])]
    except IndexError:
        return ["Nilai RGB kurang lengkap!\nContoh penggunaan: rvd rgb 0 255 255", "./saved_items/images/qmark.png"]
    except:
        return ["Sepertinya kamu tidak menginput angka RGB dengan tepat!\nContoh penggunaan: rvd rgb 0 255 255", "./saved_items/images/qmark.png"]
    
    if any(color > 255 for color in rgb_values):
        return ["Salah satu nilai dari warna RGB melebihi 255!\nPastikan nilai RGB valid!", "./saved_items/images/qmark.png"]
    hex_value = '{:02x}{:02x}{:02x}'.format(rgb_values[0], rgb_values[1], rgb_values[2])
    return await hex(hex_value) # Cheat