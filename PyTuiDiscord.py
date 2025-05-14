from textual.app import App, ComposeResult

# Import the LoginScreen from the new screens.py
# Ensure screens.py is in the same directory or adjust python path accordingly
from screens import LoginScreen 

# Constants and other specific screen/widget imports are now in screens.py
# network_fuction and asyncio are not directly used by TuiApp in this structure

class TuiApp(App):
    CSS_PATH = "pytuidiscord.tcss"  # Link the CSS file
    TITLE = "PyTuiDiscord"
    debug = True # Class variable for debug mode

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        # Consider adding a quit binding e.g. ("ctrl+c", "quit", "Quit")
    ]

    def __init__(self, debug_param: bool = True):
        super().__init__()
        # The class variable TuiApp.debug is used by default.
        # If you want instance-specific debug mode based on the param:
        # self.debug = debug_param 

    def on_ready(self) -> None:
        """Called when the app is ready to run."""
        self.push_screen(LoginScreen())
# End of TuiApp class


if __name__ == "__main__":
  app = TuiApp()
  app.run()