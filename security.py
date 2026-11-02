import hashlib,secrets
def hash_password(password):
    salt=secrets.token_hex(16); d=hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),120000); return salt+'$'+d.hex()
def verify_password(password,stored):
    try:
        salt,d=stored.split('$',1); c=hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),120000); return secrets.compare_digest(c.hex(),d)
    except Exception:return False
