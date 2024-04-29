from textual import work
from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Container
from textual.widgets import Header, Input, Button, Footer, ListView, ListItem, Label, RichLog

from PyTuiDiscord import network_fuction

# class for displaying guilds, get token as parameter
class GuildListScreen(Screen):
  def __init__(self, token):
    super().__init__()
    self.token = token
    self.guild_list = network_fuction.get_guilds(self.token)
  """widget for displaying guilds"""

  # key bindings for ListItem widget selection
  BINDINGS = [
    ("enter", "select_current", "Select current item"),
    
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
        id="left_pane",
      ),
      Container(
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

  BINDINGS = [
    ('tab', 'focus_next', 'Focus next widget'),
    ('page up', 'scroll_up', 'Scroll up'),
    ('page down', 'scroll_down', 'Scroll down'),
  ]

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
        id="left_pane",
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
    self.init_chat_log(event.item.name)

  @work(exclusive=True)
  async def init_chat_log(self, channel_id):
    chat_log = await network_fuction.get_channel_messages(self.token, channel_id, None)
    self.log("chat_log", chat_log)
    chat_log_widget = self.get_widget_by_id("chat_log")
    chat_log_widget.clear()
    chat_log_widget.write(chat_log)
# End of PerGuildMessageScreen class