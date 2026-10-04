from config import load_settings
from gui import ShellGUI

if __name__ == "__main__":
    settings, config_error = load_settings()
    ShellGUI(settings, config_error).run()