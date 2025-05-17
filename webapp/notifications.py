import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SMSNotifier:
    def __init__(self, account_sid=None, auth_token=None, from_number=None, to_number=None):
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_PHONE_NUMBER')
        self.to_number = to_number or os.getenv('NOTIFICATION_PHONE_NUMBER')
        self.client = None
        
        # Initialize Twilio client if credentials are available
        if all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("SMS notifier initialized successfully")
            except ImportError:
                logger.error("Twilio package not installed. SMS notifications will not work.")
            except Exception as e:
                logger.error(f"Error initializing SMS notifier: {str(e)}")
        else:
            logger.warning("SMS notifier not configured. Missing environment variables.")
    
    def send_alert(self, message):
        """Send an SMS alert with the given message"""
        if not self.client:
            logger.warning("SMS notifier not initialized. Cannot send alert.")
            return False
        
        try:
            # Send the SMS
            sms = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            logger.info(f"SMS alert sent successfully. SID: {sms.sid}")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS alert: {str(e)}")
            return False
