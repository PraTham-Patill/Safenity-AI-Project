import re
import os
import platform
from config import logger

def validate_phone_number(phone_number):
    """Helper function to validate and format phone numbers for Twilio"""
    if not phone_number:
        return None
        
    # Strip all non-digit characters
    digits_only = re.sub(r'\D', '', phone_number)
    
    # For Indian numbers, ensure 10 digits after removing non-digit characters
    if len(digits_only) == 10:
        return f"+91{digits_only}"
    
    # If number already starts with country code, return as is
    if phone_number.startswith('+91'):
        return phone_number
    
    # If number starts with 0, replace with +91
    if phone_number.startswith('0'):
        return f"+91{digits_only[1:]}"
    
    # If it's a full international number, return as is
    if phone_number.startswith('+'):
        return phone_number
    
    return None

def render_error_page(error_message):
    """Function to render a basic error page when template is missing"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: #f8f9fa; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #dc3545; }}
            .btn {{ display: inline-block; background-color: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Error</h1>
            <p>{error_message}</p>
            <a href="/" class="btn">Go back to home</a>
        </div>
    </body>
    </html>
    """
    return html, 500

def get_platform_specific_codec():
    """Get platform-specific video codec"""
    if platform.system() == "Windows":
        return 'MJPG'  # Better Windows compatibility
    else:
        return 'mp4v'