import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def send_alert(message):
    """Send SMS alert using Twilio
    
    Args:
        message: The message to send
        
    Returns:
        Boolean indicating success or failure
    """
    # Get Twilio credentials from environment variables
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')
    to_number = os.environ.get('NOTIFICATION_PHONE_NUMBER')
    
    # Check if all required credentials are available
    if not all([account_sid, auth_token, from_number, to_number]):
        logger.warning("Twilio credentials not configured. SMS alert not sent.")
        return False
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send message
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        logger.info(f"SMS alert sent successfully. SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending SMS alert: {e}")
        return False