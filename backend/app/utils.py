import base64 
def encode_username(username):
    return base64.urlsafe_b64encode(username.encode()).decode()

def decode_username(encoded):
    return base64.urlsafe_b64decode(encoded.encode()).decode()