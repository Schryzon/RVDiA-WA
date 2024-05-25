"""
File for handling message-based commands
Pretty much a nostalgia to Discord's!
"""
import asyncio
from dotenv import load_dotenv
import os
import sys
import openai

# Fixing module not found error
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import command_cogs
load_dotenv()

prefixes = [
    "rvd ",
    "r!",
    "!",
    "Rvd"
]

def check_command(message_body:str):
    """
    Check if the message contains a command.
    """
    for prefix in prefixes:
        prefix = prefix.lower()
        if message_body.startswith(prefix):
            message_without_prefix = message_body[len(prefix):].strip()
            # Split the message into parts
            parts = message_without_prefix.split()
            if len(parts) > 0:
                command_name = parts[0]
                args = parts[1:] or None
                return [True, (prefix, command_name, args)]
    return False

async def execute_command(command_name:str, *args):
    """
    Execute commands, pretty much like eval()
    Though, this one accepts variable args!
    """
    func = globals().get(command_name.lower()) or getattr(command_cogs, command_name.lower(), None) # Trying to make it case insensitive
    if func and callable(func):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args)
            else:
                return func(*args)
            
        except Exception as e:
            return f"Wow! Command ini mengalami error!\nDetail error: {e}\nTolong laporkan ke Jayananda segera, ya!"
    else:
        return f"No command called {command_name} found."