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
    
    response_json = {}
    try:
        response_json = response.json()
    except json.JSONDecodeError:
        # If response is not JSON, and it's not a successful status, it's an issue.
        if response.ok: # Successful status but not JSON
             return {"error": "Login successful, but server sent an unreadable response."}
        # For non-OK responses that aren't JSON, use the text content.
        return {"error": f"Server error ({response.status_code}): {response.text[:200]}"}

    # Check for captcha first, as it can come with various status codes (e.g., 200 or 400)
    if "captcha_key" in response_json:
      return {
          "captcha_required": True, 
          "message": response_json.get("message", "reCaptcha verification required."),
          "details": response_json # Pass all details (sitekey, service, rqdata, rqtoken)
      }
    
    # If not captcha, then evaluate based on HTTP status code
    if response.ok: # Status 200-299, typically means login success if token is present
      token = response_json.get("token")
      if token:
        encryption_utils.save_encrypted_token(token) # Encrypt and save the token
        return {"token": token} # Return the raw token for immediate use in the session
      else:
        # Successful status but no token. This could be an edge case or an error message.
        error_message = "Login successful, but no token was found in the response."
        if "message" in response_json: # Check if Discord included a specific message
            error_message = response_json["message"]
        # It might also have an 'errors' structure if it's a subtle error despite 2xx status
        if response_json.get("errors"):
            try:
                error_details = []
                for field, errors_list in response_json["errors"].items():
                    for error_item in errors_list:
                        error_details.append(f"{field.replace('_', ' ').capitalize()}: {error_item['message']}")
                if error_details:
                  error_message = "\n".join(error_details)
            except Exception: 
                pass # Stick with the existing error_message
        return {"error": error_message}
    else: # Not response.ok (e.g., 400 for bad credentials if not captcha, 401, 403, 5xx)
      # Attempt to parse a structured error message from Discord's JSON response
      error_message = f"Login failed (status {response.status_code})."
      needs_email_verification = False # Initialize the flag

      if "message" in response_json:
          error_message = response_json["message"]
      
      if response_json.get("errors"): # Discord often returns detailed errors in an 'errors' object
          try:
              error_details = []
              # Check for the specific email verification error
              login_errors = response_json.get("errors", {}).get("login", {}).get("_errors", [])
              for err in login_errors:
                  if err.get("code") == "ACCOUNT_LOGIN_VERIFICATION_EMAIL":
                      needs_email_verification = True
                      # Use the specific message from this error if available
                      error_message = err.get("message", error_message) 
                      break # Found the specific error, no need to parse further generic errors for the main message
              
              if not needs_email_verification: # If not the specific email error, parse other errors
                for field, errors_list in response_json["errors"].items():
                    for error_item in errors_list: # errors_list is a list of dicts
                        # Ensure error_item is a dict and has 'message'
                        if isinstance(error_item, dict) and 'message' in error_item:
                            error_details.append(f"{field.replace('_', ' ').capitalize()}: {error_item['message']}")
                        elif isinstance(error_item, str): # Sometimes it might just be a list of strings
                            error_details.append(f"{field.replace('_', ' ').capitalize()}: {error_item}")
                if error_details: # If we successfully parsed details, use them
                  error_message = "\n".join(error_details)
          except Exception: 
              # If parsing 'errors' fails, stick with the 'message' or the generic one
              pass 
      
      return_value = {"error": error_message}
      if needs_email_verification:
          return_value["needs_email_verification"] = True
      return return_value

  except requests.exceptions.RequestException as req_err: # Catches network issues, DNS failures, etc.
    return {"error": f"A network error occurred: {req_err}"}
  except Exception as e: # Catch-all for any other unexpected errors during the process
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