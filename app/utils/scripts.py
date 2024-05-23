"""
A script file, similar to scripts.main from RVDiA
"""
import aiohttp
import logging
import aiofiles
from quart import current_app, jsonify

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
                        print("Media ID:", media_id)
                        return media_id
                    else:
                        print("Status:", response.status)
                        print("Response:", await response.text())
        except aiohttp.ClientConnectorError as e:
            print("Connection Error:", str(e))