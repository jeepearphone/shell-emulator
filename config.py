import argparse
import xml.etree.ElementTree as ET


class ConfigError(Exception):
    """Ошибка чтения конфигурационного файла."""


def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор оболочки")
    parser.add_argument("--vfs", help="путь к физическому расположению VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    parser.add_argument("--config", help="путь к XML-файлу конфигурации")
    return parser.parse_args()


def read_xml_config(path):
    """Читает XML и возвращает словарь {'vfs': ..., 'script': ...}."""
    try:
        tree = ET.parse(path)
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}")
    except ET.ParseError as e:
        raise ConfigError(f"invalid XML in '{path}': {e}")
    except OSError as e:
        raise ConfigError(f"cannot read config '{path}': {e}")

    root = tree.getroot()
    if root.tag != "config":
        raise ConfigError(f"root element must be <config>, got <{root.tag}>")

    return {
        "vfs": (root.findtext("vfs_path") or "").strip() or None,
        "script": (root.findtext("startup_script") or "").strip() or None,
    }


def load_settings():
    """Собирает итоговые настройки. Возвращает (settings, текст_ошибки_или_None)."""
    args = parse_args()

    from_file = {"vfs": None, "script": None}
    error = None
    if args.config:
        try:
            from_file = read_xml_config(args.config)
        except ConfigError as e:
            error = str(e)

    settings = {
        "config": args.config,
        # командная строка важнее файла
        "vfs": args.vfs if args.vfs is not None else from_file["vfs"],
        "script": args.script if args.script is not None else from_file["script"],
    }
    return settings, error