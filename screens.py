from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Container
from textual.widgets import Button, Footer, Header, Input, ListItem, ListView, Label, RichLog, Static
import network_fuction
import asyncio # Added for asyncio.to_thread
from encryption_utils import save_encrypted_token # For ManualTokenInputScreen

# Assuming constants.py is in the same directory
from constants import (
    ID_EMAIL_INPUT,
    ID_PASSWORD_INPUT,
    ID_LOGIN_BUTTON,
    ID_ERROR_LABEL,
    ID_GUILD_LIST_VIEW,
    ID_CHANNEL_LIST_VIEW,
    ID_CHAT_LOG,
    ID_CHAT_INPUT,
    ID_INFO_LABEL,
)

# (ID_MANUAL_TOKEN_INPUT and ID_SUBMIT_TOKEN_BUTTON will be added to constants.py later)
ID_MANUAL_TOKEN_INPUT = "manual_token_input"
ID_SUBMIT_TOKEN_BUTTON = "submit_token_button"

class ManualTokenInputScreen(Screen):
    """Screen for manually inputting a Discord token."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("reCaptcha detected or login failed. Please obtain your token manually."),
            Label("You can find it in your browser's developer tools (Network tab, look for '/api/v9/users/@me' requests under 'authorization' header after logging in via browser)."),
            Input(placeholder="Enter your Discord token here", id=ID_MANUAL_TOKEN_INPUT),
            Button("Submit Token", id=ID_SUBMIT_TOKEN_BUTTON, variant="primary"),
            Label("", id=ID_ERROR_LABEL), # Re-use error label ID or a new one
            id="manual_token_container" # Added ID for styling
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == ID_SUBMIT_TOKEN_BUTTON:
            token_input_widget = self.query_one(f"#{ID_MANUAL_TOKEN_INPUT}", Input)
            token = token_input_widget.value.strip()
            error_label_widget = self.query_one(f"#{ID_ERROR_LABEL}", Label)

            if not token:
                error_label_widget.update("Token cannot be empty.")
                return

            try:
                # Save the manually entered token (it will be encrypted by this function)
                save_encrypted_token(token)
                self.log.info("Manual token saved successfully.")
                error_label_widget.update("Token saved. Proceeding to guilds...")
                
                # Short delay to show message then switch
                await asyncio.sleep(1) 
                
                # Assuming GuildListScreen is the next logical screen
                # We need to ensure GuildListScreen can be instantiated without a token if it's read from file
                # Or, pass the token directly if that's how GuildListScreen is designed
                self.app.pop_screen() # Pop ManualTokenInputScreen
                self.app.push_screen(GuildListScreen(token=token)) # Pass the raw token for this session

            except Exception as e:
                self.log.error(f"Error saving manual token: {e}")
                error_label_widget.update(f"Failed to save token: {e}")

class LoginScreen(Screen):
  """Screen for user login."""
  
  def compose(self) -> ComposeResult:
    """Compose the login screen UI."""
    yield Header()
    # The Container helps with centering and applying border via CSS
    with Container():
        yield Input(id=ID_EMAIL_INPUT, placeholder="Email")
        yield Input(id=ID_PASSWORD_INPUT, placeholder="Password", password=True)
        yield Button("Login", id=ID_LOGIN_BUTTON, variant="primary")
        # Removed classes="error-message"
        self.error_label = Label("", id=ID_ERROR_LABEL) 
        yield self.error_label
    yield Footer()

  def on_mount(self) -> None:
    """Check for existing token on mount and attempt auto-login."""
    try:
      # network_fuction.get_saved_token() will load and decrypt
      token = network_fuction.get_saved_token() 
      if token:
        self.log.info("Decrypted token found, attempting to switch to GuildListScreen.")
        # Ensure GuildListScreen can handle being pushed like this
        # It expects a token in its __init__
        self.app.push_screen(GuildListScreen(token=token))
      else:
        self.log.info("No saved token found or decryption failed. User needs to log in or provide token.")
    except Exception as e:
      self.log.error(f"Error checking for saved token: {e}")
      self.error_label.update("Error loading saved session. Please log in.")

  async def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handles login button press."""
    login_response = {} # Initialize login_response
    if event.button.id == ID_LOGIN_BUTTON:
      email_input = self.query_one(f"#{ID_EMAIL_INPUT}", Input)
      password_input = self.query_one(f"#{ID_PASSWORD_INPUT}", Input)
      client_id = email_input.value
      client_secret = password_input.value

      if not client_id or not client_secret:
        self.error_label.update("Email and password cannot be empty.")
        return

      self.error_label.update("Logging in...") 
      email_input.disabled = True
      password_input.disabled = True
      event.button.disabled = True

      try:
        # network_fuction.get_login_info now returns a dict
        login_response = await asyncio.to_thread(network_fuction.get_login_info, client_id, client_secret)
        
        if login_response.get("captcha_required"):
            self.log.warning(f"Login attempt resulted in reCaptcha: {login_response.get('message')}")
            self.error_label.update("reCaptcha required. Please provide token manually.")
            self.app.push_screen(ManualTokenInputScreen())
        elif login_response.get("token"):
            token = login_response["token"]
            self.log.info("Login successful. Token obtained.")
            self.error_label.update("") 
            # GuildListScreen expects the raw token for the session
            self.app.push_screen(GuildListScreen(token=token))
        elif login_response.get("error"):
            error_msg = login_response["error"]
            self.log.error(f"Login failed: {error_msg}")
            self.error_label.update(f"Login failed: {error_msg}")
        else:
            self.log.error("Login failed due to an unknown issue. No token, captcha, or error in response.")
            self.error_label.update("Login failed. Unknown error.")

      except Exception as e:
        self.log.error(f"Login error: {e}")
        self.error_label.update(f"An error occurred: {e}")
      finally:
        # Re-enable inputs only if not navigating away or to manual token screen
        # This logic might need refinement based on screen transition flow
        if not (login_response.get("captcha_required") or login_response.get("token")) :
            email_input.disabled = False
            password_input.disabled = False
            event.button.disabled = False
        else: # If we are moving to another screen, keep them disabled
            pass

class GuildListScreen(Screen):
  """Screen for displaying a list of guilds (servers)."""
  def __init__(self, token: str):
    super().__init__()
    self.token = token
    self.guild_list = [] 

  BINDINGS = [
    ("enter", "select_current_guild", "Select current guild") 
  ]

  def compose(self) -> ComposeResult:
    """Compose the guild list screen UI."""
    yield Header()
    yield Horizontal(
      # Assign ID for specific styling if .left-pane class is too general
      Container(
        ListView(id=ID_GUILD_LIST_VIEW), 
        id="guild_list_left_pane" # Using ID instead of classes
      ),
      # Added a placeholder container for potential right-side content or to ensure layout
      Container(id="guild_list_right_pane") 
    )
    # Removed classes="info-message"
    self.info_label = Static("", id=ID_INFO_LABEL) 
    yield self.info_label
    yield Footer()

  async def on_mount(self) -> None:
    """Fetch guilds when the screen is mounted."""
    self.query_one(f"#{ID_GUILD_LIST_VIEW}", ListView).disabled = True 
    self.info_label.update("Loading guilds...")
    self.fetch_guilds() 

  @work(exclusive=True)
  async def fetch_guilds(self) -> None:
    """Fetches guild list from the network and populates the ListView."""
    guild_list_view = self.query_one(f"#{ID_GUILD_LIST_VIEW}", ListView)
    try:
      guild_data = await asyncio.to_thread(network_fuction.get_guilds, self.token)
      guild_list_view.clear() 
      if guild_data:
        self.guild_list = guild_data
        for guild in self.guild_list:
          guild_list_view.append(
            ListItem(
              Label(guild.get("name", "Unknown Guild")), 
              name=str(guild.get("id")) 
            )
          )
        self.info_label.update("") 
        self.log.info(f"Fetched {len(self.guild_list)} guilds.")
      else:
        self.info_label.update("No guilds found or failed to load guilds.")
        self.log.info("No guilds data received.")
    except Exception as e:
      self.log.error(f"Error fetching guilds: {e}")
      self.info_label.update(f"Error fetching guilds. Check logs.")
    finally:
      guild_list_view.disabled = False
      if not guild_list_view.children: 
          self.info_label.update("No guilds to display.")

  async def on_list_view_selected(self, event: ListView.Selected) -> None:
    """Handles guild selection from the ListView."""
    if event.list_view.id == ID_GUILD_LIST_VIEW and event.item and event.item.name:
      selected_guild_id = event.item.name
      self.log.info(f"Guild selected: ID {selected_guild_id}")
      self.app.push_screen(PerGuildMessageScreen(guild_id=selected_guild_id, token=self.token))
    else:
      self.log.warning("Guild selection event with no item name or wrong list view.")

class PerGuildMessageScreen(Screen):
  """Screen for displaying channels and messages within a specific guild."""
  def __init__(self, guild_id: str, token: str):
    super().__init__()
    self.guild_id = guild_id
    self.token = token
    self.channel_list = [] 
    self.current_channel_id: str | None = None 

  def compose(self) -> ComposeResult:
    """Compose the per-guild message screen UI."""
    yield Header()
    yield Horizontal(
      # Assign ID for specific styling
      Container(
        ListView(id=ID_CHANNEL_LIST_VIEW), 
        id="channel_list_left_pane" # Using ID instead of classes
      ),
      Container(
        # ID_CHAT_LOG is already "chat_history" as per constants.py, CSS uses #chat_history
        RichLog(id=ID_CHAT_LOG, auto_scroll=True, wrap=True, highlight=True, markup=True), 
        Input(id=ID_CHAT_INPUT, placeholder="Type your message here..."),
        id="chat_area_container" # Added ID for the right container
      )
    )
    # Removed classes="info-message"
    self.info_label = Static("", id=ID_INFO_LABEL) 
    yield self.info_label
    yield Footer()

  async def on_mount(self) -> None:
    """Fetch channels when the screen is mounted."""
    self.query_one(f"#{ID_CHANNEL_LIST_VIEW}", ListView).disabled = True
    self.info_label.update(f"Loading channels for guild {self.guild_id}...")
    self.fetch_channels() 

  @work(exclusive=True)
  async def fetch_channels(self) -> None:
    """Fetches channel list for the current guild and populates the ListView."""
    channel_list_view = self.query_one(f"#{ID_CHANNEL_LIST_VIEW}", ListView)
    try:
      channel_data = await asyncio.to_thread(network_fuction.get_channels, self.token, self.guild_id)
      channel_list_view.clear()
      if channel_data:
        self.channel_list = channel_data
        for channel in self.channel_list:
          channel_list_view.append(
            ListItem(
              Label(channel.get("name", "Unknown Channel")), 
              name=str(channel.get("id"))
            )
          )
        self.info_label.update("")
        self.log.info(f"Fetched {len(self.channel_list)} channels for guild {self.guild_id}.")
      else:
        self.info_label.update("No channels found or failed to load channels.")
        self.log.info(f"No channel data received for guild {self.guild_id}.")
    except Exception as e:
      self.log.error(f"Error fetching channels for guild {self.guild_id}: {e}")
      self.info_label.update(f"Error fetching channels. Check logs.")
    finally:
      channel_list_view.disabled = False
      if not channel_list_view.children:
          self.info_label.update("No channels to display.")

  async def on_list_view_selected(self, event: ListView.Selected) -> None:
    """Handles channel selection and triggers message loading."""
    if event.list_view.id == ID_CHANNEL_LIST_VIEW and event.item and event.item.name:
      self.current_channel_id = event.item.name
      self.log.info(f"Channel selected: ID {self.current_channel_id} in guild {self.guild_id}")
      chat_log_widget = self.query_one(f"#{ID_CHAT_LOG}", RichLog)
      chat_log_widget.clear() 
      chat_log_widget.write("Loading messages...")
      self.update_chat_log(self.current_channel_id) 
      self.query_one(f"#{ID_CHAT_INPUT}", Input).focus() 
    else:
      self.log.warning("Channel selection event with no item name or wrong list view.")

  @work(exclusive=True)
  async def update_chat_log(self, channel_id: str) -> None:
    """Fetches and displays messages for the selected channel."""
    if not channel_id:
      self.log.warning("update_chat_log called with no channel_id.")
      return

    chat_log_widget = self.query_one(f"#{ID_CHAT_LOG}", RichLog)
    try:
      # Assuming get_channel_messages is synchronous as per previous corrections
      messages_data = await asyncio.to_thread(network_fuction.get_channel_messages, self.token, channel_id, None)
      chat_log_widget.clear() 
      if messages_data:
        if isinstance(messages_data, list) and not messages_data: 
             chat_log_widget.write("No messages in this channel.")
        elif isinstance(messages_data, list):
          for message_item in reversed(messages_data): # Display newest messages at the bottom
            if isinstance(message_item, dict): 
              author = message_item.get('author', {}).get('username', 'System') # Get username from author object
              content = message_item.get('content', '')
              chat_log_widget.write(f"[b]{author}[/b]: {content}")
            else: 
              chat_log_widget.write(str(message_item))
          self.log.info(f"Chat log updated for channel {channel_id} with {len(messages_data)} messages.")
        else: 
          chat_log_widget.write(str(messages_data))
          self.log.info(f"Chat log updated for channel {channel_id} with single data block.")
      else: 
        chat_log_widget.write("No messages in this channel or failed to load.")
        self.log.info(f"No messages data received for channel {channel_id}.")
    except Exception as e:
      self.log.error(f"Error fetching/displaying messages for channel {channel_id}: {e}")
      chat_log_widget.write(f"Error loading messages. Check logs.")

  async def on_input_submitted(self, event: Input.Submitted) -> None:
    """Handles message submission from the chat input."""
    if event.input.id == ID_CHAT_INPUT and self.current_channel_id:
      message_content = event.value.strip() 
      if not message_content: 
        return

      self.log.info(f"Attempting to send message to channel {self.current_channel_id}: {message_content}")
      chat_input_widget = self.query_one(f"#{ID_CHAT_INPUT}", Input)
      original_placeholder = chat_input_widget.placeholder
      chat_input_widget.placeholder = "Sending..."
      chat_input_widget.disabled = True

      try:
        # Assuming network_fuction.send_message is synchronous and needs to be implemented
        # For now, let's assume it might raise an error or return False if not implemented
        if hasattr(network_fuction, 'send_message'):
            success = await asyncio.to_thread(network_fuction.send_message, self.token, self.current_channel_id, message_content)
        else:
            self.log.error("network_fuction.send_message is not implemented.")
            success = False # Simulate failure
        
        if success:
          self.log.info(f"Message sent successfully to channel {self.current_channel_id}.")
          chat_input_widget.value = "" 
          # Refresh chat log to show the new message. 
          # Calling self.update_chat_log() directly might not be ideal if send_message itself triggers an update (e.g., via websocket)
          # For now, we'll explicitly refresh.
          self.update_chat_log(self.current_channel_id)
        else:
          self.log.error(f"Failed to send message to channel {self.current_channel_id}.")
          self.query_one(f"#{ID_CHAT_LOG}", RichLog).write("[red]System: Failed to send message (or function not implemented).[/red]")
      except Exception as e:
        self.log.error(f"Error sending message to channel {self.current_channel_id}: {e}")
        self.query_one(f"#{ID_CHAT_LOG}", RichLog).write(f"[red]System: Error sending message - {e}[/red]")
      finally:
        chat_input_widget.disabled = False
        chat_input_widget.placeholder = original_placeholder
        chat_input_widget.focus()
