"""Точка входа: читает настройки и открывает окно эмулятора."""

from config import load_settings
from gui import ShellGUI


def main():
    """Запускает эмулятор с параметрами из командной строки и XML."""
    settings, config_error = load_settings()
    ShellGUI(settings, config_error).run()


if __name__ == "__main__":
    main()