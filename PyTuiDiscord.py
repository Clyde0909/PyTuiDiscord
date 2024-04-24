from textual import work
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Container
from textual.widgets import Button, Footer, Header, Input, ListItem, ListView, Label, RichLog
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
# End of LoginScreen class

# class for displaying guilds, get token as parameter
class GuildListScreen(Screen):
  def __init__(self, token):
    super().__init__()
    self.token = token
    self.guild_list = network_fuction.get_guilds(self.token)
  """widget for displaying guilds"""

  # key bindings for ListItem widget selection
  BINDINGS = [
    ("enter", "select_current", "Select current item")
  ]

  def compose(self) -> ComposeResult:
    yield Header()
    yield Horizontal(
      Container(
        ListView(
          id="guild_list",
          *[
            ListItem(
              Label(guild["name"]),
              name=str(guild["id"]),
              # add method for ListItem widget to select
            )
            for guild in self.guild_list
          ]
        ),
        classes="left-pane"
      ),
      Container(
        Button("Get Channels", id="get_channels")
      )
    )
    yield Footer()

  def on_list_view_selected(self, event: ListView.Selected) -> None:
    # self.log("selected", event.item.name)
    self.app.push_screen(PerGuildMessageScreen(event.item.name, self.token))

  def on_mount(self) -> None:
    pass
# End of GuildListScreen class

class PerGuildMessageScreen(Screen):
  """widget for displaying channels"""
  def __init__(self, guild_id, token):
    super().__init__()
    self.guild_id = guild_id
    self.token = token
    self.channel_list = network_fuction.get_channels(self.token, self.guild_id)
    self.log("channel_list", self.channel_list)

  def compose(self) -> ComposeResult:
    yield Header()
    yield Horizontal(
      Container(
        ListView(
          id="channel_list",
          *[
            ListItem(
              Label(channel["name"]),
              name=str(channel["id"]),
            )
            for channel in self.channel_list
          ]
        ),
        classes="left-pane"
      ),
      Container(
        RichLog(id="chat_log", auto_scroll=True),
        Input(id="chat_input", placeholder="Type your message here"),
      )
    )
    yield Footer()

  def on_list_view_selected(self, event: ListView.Selected) -> None:
    self.log("selected", event.item.name)
    # await get_channel_messages(token, event.item.name, None)
    self.update_chat_log(event.item.name)

  @work(exclusive=True)
  async def update_chat_log(self, channel_id):
    chat_log = await network_fuction.get_channel_messages(self.token, channel_id, None)
    self.log("chat_log", chat_log)
    self.get_widget_by_id("chat_log").write(chat_log)
# End of PerGuildMessageScreen class


class TuiApp(App):
  def __init__(self, debug: bool = True):
    super().__init__()

  BINDINGS = [
    ("d", "toggle_dark", "Toggle dark mode"),
  ]

  debug = True

  def on_ready(self) -> None:
    self.push_screen(LoginScreen())
# End of TuiApp class


if __name__ == "__main__":
  app = TuiApp()
  app.run()