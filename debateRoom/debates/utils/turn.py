import time
import hmac
import hashlib
import base64

TURN_SECRET = b"MY_SECRET_KEY_vasu333"  # Same as Coturn config
TURN_REALM = "debateplatform.com"          # Same as Coturn realm

def generate_turn_credentials(expiry=3600):
    username = str(int(time.time()) + expiry)
    digest = hmac.new(TURN_SECRET, username.encode('utf-8'), hashlib.sha1).digest()
    credential = base64.b64encode(digest).decode('utf-8')
    
    return {
        "username": username,
        "credential": credential,
        "urls": ["turn:turn.debateplatform.com:3478"], 
        "realm": TURN_REALM
    }