from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, RECIPIENT_PHONE_NUMBER, SMS_ENABLED, logger
from utils import validate_phone_number

def send_sms_alert(crime_class, prediction_score, timestamp, suspect_count, weapon_detected):
    """Send SMS alert for crime detection"""
    try:
        # Check if SMS is enabled
        if not SMS_ENABLED:
            print("⚠️ SMS alerts disabled: Missing Twilio credentials or recipient number")
            return False
            
        # Validate and format phone numbers
        from_number = validate_phone_number(TWILIO_PHONE_NUMBER)
        to_number = validate_phone_number(RECIPIENT_PHONE_NUMBER)
        
        if not from_number or not to_number:
            print(f"⚠️ Invalid phone number format. From: {TWILIO_PHONE_NUMBER}, To: {RECIPIENT_PHONE_NUMBER}")
            return False
            
        # Prepare SMS message content
        message = (
            f"🚨 CRIME ALERT: {crime_class} detected with {prediction_score:.2f}% confidence. "
            f"Time: {timestamp}. "
            f"Suspects: {suspect_count}. "
            f"Weapon: {'Yes' if weapon_detected else 'No'}. "
            f"Check dashboard for details."
        )
        
        # Send SMS using Twilio
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            sms = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            print(f"✅ SMS alert sent successfully! SID: {sms.sid}")
            return True
        except Exception as e:
            print(f"⚠️ Twilio SMS error: {str(e)}")
            return False
                
    except Exception as e:
        print(f"⚠️ Error preparing SMS: {str(e)}")
        return False

def send_sms_via_twilio(to_number, message):
    """Send SMS via Twilio with comprehensive error handling"""
    # Check Twilio credentials
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logger.error("Incomplete Twilio credentials")
        return False, "Incomplete Twilio configuration"

    try:
        # Validate numbers
        from_number = validate_phone_number(TWILIO_PHONE_NUMBER)
        to_number = validate_phone_number(to_number)

        if not from_number or not to_number:
            logger.error(f"Invalid phone numbers. From: {from_number}, To: {to_number}")
            return False, "Invalid phone number format"

        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Send message
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )

        logger.info(f"SMS sent successfully to {to_number}. SID: {message.sid}")
        return True, message.sid

    except TwilioRestException as e:
        logger.error(f"Twilio Error: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Unexpected error sending SMS: {e}")
        return False, "Unexpected error sending SMS"