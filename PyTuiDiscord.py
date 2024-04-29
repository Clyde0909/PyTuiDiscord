from textual.app import App

# import network functions
import network_fuction

# import screen classes
from Screen import login, guild

class TuiApp(App):
  def __init__(self, debug: bool = True):
    super().__init__()

  CSS_PATH = "./CSS/global.tcss"

  BINDINGS = [
    ("d", "toggle_dark", "Toggle dark mode"),
  ]

  debug = True

  def on_ready(self) -> None:
    self.push_screen(login.LoginScreen())
# End of TuiApp class


if __name__ == "__main__":
  app = TuiApp()
  app.run()