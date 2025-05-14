\
import os
from cryptography.fernet import Fernet, InvalidToken

KEY_FILE = "secret.key"
ENV_FILE = ".env" # Assuming your token is stored in .env

def generate_key():
    """Generates a new Fernet key and saves it to KEY_FILE.
    If ENV_FILE exists, it will be deleted as the old token cannot be decrypted with a new key.
    """
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
    
    if os.path.exists(ENV_FILE):
        try:
            os.remove(ENV_FILE)
            print(f"Generated new encryption key. Old {ENV_FILE} has been removed.")
        except OSError as e:
            print(f"Error removing old {ENV_FILE} after new key generation: {e}")
    return key

def load_key():
    """Loads the Fernet key from KEY_FILE. If it doesn't exist, generates a new one."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        return generate_key()

def encrypt_token(token: str) -> bytes:
    """Encrypts a token string using the Fernet key."""
    key = load_key()
    f = Fernet(key)
    encrypted_token = f.encrypt(token.encode())
    return encrypted_token

def decrypt_token(encrypted_token: bytes) -> str | None:
    """Decrypts an encrypted token (bytes) using the Fernet key.
    Returns the decrypted token as a string, or None if decryption fails.
    """
    key = load_key()
    f = Fernet(key)
    try:
        decrypted_token = f.decrypt(encrypted_token)
        return decrypted_token.decode()
    except InvalidToken:
        print("Failed to decrypt token: Invalid token or key.")
        # If decryption fails, it's good to remove the potentially corrupt/old .env file
        if os.path.exists(ENV_FILE):
            try:
                os.remove(ENV_FILE)
                print(f"Removed {ENV_FILE} due to decryption error.")
            except OSError as e:
                print(f"Error removing {ENV_FILE} after decryption error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during token decryption: {e}")
        return None

def save_encrypted_token(token: str):
    """Encrypts the given token and saves it to the ENV_FILE."""
    encrypted_token_bytes = encrypt_token(token)
    try:
        with open(ENV_FILE, "w") as file: # Write bytes as base64 string for text file
            file.write(f"DISCORD_TOKEN={encrypted_token_bytes.decode('latin-1')}") # Fernet output is urlsafe base64
        print(f"Token encrypted and saved to {ENV_FILE}")
    except IOError as e:
        print(f"Error writing encrypted token to {ENV_FILE}: {e}")


def load_decrypted_token() -> str | None:
    """Loads and decrypts the token from ENV_FILE."""
    if not os.path.exists(ENV_FILE):
        return None
    try:
        with open(ENV_FILE, "r") as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("DISCORD_TOKEN="):
                    encrypted_token_str = line.split("=", 1)[1].strip()
                    # Encrypted token was saved as base64 string, convert back to bytes
                    encrypted_token_bytes = encrypted_token_str.encode('latin-1')
                    return decrypt_token(encrypted_token_bytes)
        return None # No token found in file
    except FileNotFoundError:
        return None
    except IOError as e:
        print(f"Error reading {ENV_FILE}: {e}")
        return None
