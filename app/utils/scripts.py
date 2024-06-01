"""
A script file, similar to scripts.main from RVDiA
"""
import aiohttp
import logging
import types
import aiofiles
import inspect
from quart import current_app
from command_cogs import (
    general,
    utility
)

categories = [general, utility]

def heading(direction:int):
        result =[]
        ranges = [
        [0, 45, "Utara"], [46, 90, "Timur Laut"],
        [91, 135, "Timur"], [136, 180, "Tenggara"],
        [181, 225, "Selatan"], [226, 270, "Barat Daya"],
        [271, 315, "Barat"], [316, 360, "Barat Laut"]
        ]

        for i in ranges:
            if direction in range(i[0], i[1] + 1):
                result.append(i[2])

        return result[0] 

async def upload_media(file_path):
    headers = {
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/media"

    async with aiohttp.ClientSession() as session:
        try:
            # Read file content asynchronously
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()

                # Construct the form data
                form_data = aiohttp.FormData()
                form_data.add_field('file', file_content, filename='variation.png', content_type='image/png')
                form_data.add_field('messaging_product', 'whatsapp')

                # Send the request
                async with session.post(url, data=form_data, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        media_id = data.get('id')
                        return media_id
                    else:
                        logging.info(f"Status: {response.status}")
                        logging.info(f"Response: {await response.text()}")
        except aiohttp.ClientConnectorError as e:
            logging.warning(f"Connection Error: {e}")

# For rvd help command
blacklisted_functions = [
    "crop_to_square",
    "say",
    "help",
    "greet"
    ]

def get_all_commands(module: types.ModuleType):
    """
    Get all function names and their docstrings from the specified module.

    Args:
    module (module): The module to inspect.

    Returns:
    list of str: A list of strings, each containing a function name and its docstring.
    """
    functions_info = []
    functions_info.append(f"-Kategori: {module.__name__.title().replace('Command_Cogs.', '')}-\n")
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if func.__module__ == module.__name__ and not name in blacklisted_functions:  # Ensure it's a function from the module, not an imported one
            docstring = inspect.getdoc(func) or "Belum ada deskripsi."
            params = inspect.signature(func).parameters
            param_list = [str(param) for param in params.values()] or ['Tidak ada']
            functions_info.append(f"*rvd {name}*\n\"{docstring}\"\nParameter dibutuhkan: {', '.join(param_list)}\n")
    return functions_info

def process_help_command():
    help_strings = []
    for category in categories:
        help_strings.extend(get_all_commands(category))
    return help_strings