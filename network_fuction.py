import requests

def check_env_file():
  # check if .env file exists
  try:
    with open(".env", "r") as file:
      lines = file.readlines()
      for line in lines:
        if "DISCORD_TOKEN" in line:
          token = line.split("=")[1].strip()
      return token
  except FileNotFoundError:
    return False

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
  response = requests.post(login_api_url, headers=headers, json=payload)
  response_json = response.json()

  with open(".env", "w") as file:
    file.write(f"DISCORD_TOKEN={response_json['token']}")
  token = response_json["token"]
  return token
  # End of get_login_info()

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

async def get_channel_messages(token, channel_id, message_id):
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