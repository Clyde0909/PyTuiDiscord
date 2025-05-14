import requests
import json # Import json for parsing response content if not already text
import encryption_utils # Changed from relative to direct import

# Renamed from check_env_file to better reflect its new role
def get_saved_token() -> str | None:
  """Loads and decrypts the token from the environment file using encryption_utils."""
  return encryption_utils.load_decrypted_token()

def get_login_info(client_id, client_secret):
  # get token from discord
  login_api_url = "https://discord.com/api/v9/auth/login"
  payload = {
    "gift_code_sku_id": None,
    "login": client_id,
    "login_source": None,
    "password": client_secret,
    "undelete": "false"
  }
  headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
  }
  
  try:
    response = requests.post(login_api_url, headers=headers, json=payload)
    response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
    response_json = response.json()

    if "captcha_key" in response_json: # Check for reCaptcha indicator
      # You might want to return more details if the API provides them (e.g., sitekey)
      return {"captcha_required": True, "message": response_json.get("message", "reCaptcha verification required.")}
    
    token = response_json.get("token")
    if token:
      encryption_utils.save_encrypted_token(token) # Encrypt and save the token
      return {"token": token} # Return the raw token for immediate use in the session
    else:
      # Handle cases where login fails without a token and without captcha (e.g., wrong credentials)
      error_message = "Login failed. Please check your credentials."
      if "message" in response_json:
          error_message = response_json["message"]
      elif response_json.get("errors"):
          # Discord often returns detailed errors in an 'errors' object
          try:
              # Attempt to format errors nicely
              error_details = []
              for field, errors_list in response_json["errors"].items():
                  for error_item in errors_list:
                      error_details.append(f"{field.replace('_', ' ').capitalize()}: {error_item['message']}")
              error_message = "\n".join(error_details) if error_details else error_message
          except Exception: # Fallback if error structure is unexpected
              pass # Keep the generic error_message
      return {"error": error_message}

  except requests.exceptions.HTTPError as http_err:
    # Try to parse the error response from Discord if available
    try:
        error_json = http_err.response.json()
        message = error_json.get("message", str(http_err))
        if "errors" in error_json: # More specific errors
             # Attempt to format errors nicely
            error_details = []
            for field, errors_list in error_json["errors"].items():
                for error_item in errors_list:
                    error_details.append(f"{field.replace('_', ' ').capitalize()}: {error_item['message']}")
            message = "\n".join(error_details) if error_details else message
        return {"error": f"Login request failed: {message}"}
    except json.JSONDecodeError: # If response is not JSON
        return {"error": f"Login request failed: {http_err}"}
  except requests.exceptions.RequestException as req_err:
    return {"error": f"A network error occurred: {req_err}"}
  except Exception as e:
    # Catch any other unexpected errors during the process
    return {"error": f"An unexpected error occurred during login: {e}"}

def get_guilds(token):
  # get guilds from discord
  guilds_api_url = "https://discord.com/api/v9/users/@me/guilds"
  headers = {
    "Authorization": token
  }
  response = requests.get(guilds_api_url, headers=headers)
  guild_list_dict = response.json()
  return guild_list_dict
  # End of get_guilds()

def get_channels(token, guild_id):
  # get channels from discord
  channels_api_url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"
  headers = {
    "Authorization": token
  }
  response = requests.get(channels_api_url, headers=headers)
  channels_list_dict = response.json()
  return channels_list_dict
  # End of get_channels()

def get_channel_messages(token, channel_id, message_id): # Removed async
  # get chattings from discord channel
  messages_api_url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
  headers = {
    "Authorization": token
  }
  if message_id:
    payload = {
      "limit": 50,
      "before": message_id
    }
  else:
    payload = {
      "limit": 50
    }
  response = requests.get(messages_api_url, headers=headers, params=payload)
  messages_list_dict = response.json()
  return messages_list_dict