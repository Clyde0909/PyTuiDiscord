from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, ListItem, ListView, Label
import network_fuction


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
      self.app.push_screen(GuildListScreen(token=token))

  def on_button_pressed(self, event: Button.Pressed) -> None:
    # get client_id and client_secret from Input widgets
    client_id = self.get_widget_by_id("email").value
    client_secret = self.get_widget_by_id("password").value
    token = network_fuction.get_login_info(client_id, client_secret)
    if(token != None):
      self.app.pop_screen()
      self.app.push_screen(GuildListScreen(token=token))
  

class GuildListScreen(Screen):
  def __init__(self, token: str):
    super().__init__()
    self.token = token
    self.guild_list = network_fuction.get_guilds(self.token)
  """widget for displaying guilds"""

  # key bindings for ListItem widget
  BINDINGS = [
    ("enter", "get_channels", "Get channels for selected guild")
  ]

  def compose(self) -> ComposeResult:
    yield Header()
    # build ListView with guild_list. ListView(ListItem(Label("One")),ListItem(Label("Two")),ListItem(Label("Three")))
    yield ListView(
      *[
        ListItem(
          Label(guild["name"]),
          name=str(guild["id"]),
        )
        for guild in self.guild_list
      ]
    )
    yield Footer()
    yield Button("Get Guilds", id="get_guilds")

  def on_mount(self) -> None:
    pass

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "get_guilds":
      # token = self.app.get_login_info()
      # guilds = network_fuction.get_guilds(token)
      self.app.push_screen(ChannelListScreen())

class ChannelListScreen(Screen):
  """widget for displaying channels"""
  def compose(self) -> ComposeResult:
    yield Header()
    yield Footer()
    yield Button("Get Channels", id="get_channels")

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "get_channels":
      # token = self.app.get_login_info()
      # channels = network_fuction.get_channels(token)
      self.app.push_screen(MessageScreen())

class MessageScreen(Screen):
  """widget for displaying messages"""
  def compose(self) -> ComposeResult:
    yield Header()
    yield Footer()
    yield Button("Get Messages", id="get_messages")

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "get_messages":
      # token = self.app.get_login_info()
      # messages = network_fuction.get_messages(token)
      self.app.pop_screen()
      # self.app.push_screen(LoginScreen())

class TuiApp(App):
  def __init__(self, debug: bool = True):
    super().__init__()

  BINDINGS = [
    ("d", "toggle_dark", "Toggle dark mode"),
  ]

  debug = True

  def on_ready(self) -> None:
    self.push_screen(LoginScreen())


if __name__ == "__main__":
  app = TuiApp()
  app.run()