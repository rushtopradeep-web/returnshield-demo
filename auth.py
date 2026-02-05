import hashlib, secrets, smtplib

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def verify(p, h):
    return hash_pw(p) == h

def reset_token():
    return secrets.token_hex(16)

def send_reset(email, token):
    # simple demo mailer – works with any SMTP later
    print("RESET LINK:", token, "for", email)
