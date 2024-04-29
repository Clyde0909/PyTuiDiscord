from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Input, Button, Footer

from PyTuiDiscord import network_fuction

from Screen import guild

class LoginScreen(Screen):
  """widget for logging in"""
  
  def compose(self) -> ComposeResult:
    yield Header()
    yield Input(id="email", placeholder="Email")
    yield Input(id="password", placeholder="Password", password=True)
    yield Button("Login", id="login")
    yield Footer()

  def on_mount(self) -> None:
    token = network_fuction.check_env_file()
    if(token):
      self.app.pop_screen()
      # return token
      self.app.push_screen(guild.GuildListScreen(token=token))

  def on_button_pressed(self, event: Button.Pressed) -> None:
    # get client_id and client_secret from Input widgets
    client_id = self.get_widget_by_id("email").value
    client_secret = self.get_widget_by_id("password").value
    token = network_fuction.get_login_info(client_id, client_secret)
    if(token != None):
      self.app.pop_screen()
      # return token
      self.app.push_screen(guild.GuildListScreen(token=token))
# End of LoginScreen class