"""Параметры командной строки и конфигурационного файла XML."""

import argparse
import xml.etree.ElementTree as ElementTree

CONFIG_ROOT_TAG = "config"


class ConfigError(Exception):
    """Ошибка чтения конфигурационного файла."""


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки")
    parser.add_argument("--vfs", help="путь к физическому расположению VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    parser.add_argument("--config", help="путь к XML-файлу конфигурации")
    return parser.parse_args(argv)


def text_or_none(root, tag):
    """Возвращает текст элемента без пробелов или None, если он пуст."""
    return (root.findtext(tag) or "").strip() or None


def read_xml_config(path):
    """Читает XML-файл и возвращает словарь {'vfs': ..., 'script': ...}."""
    try:
        tree = ElementTree.parse(path)
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}")
    except ElementTree.ParseError as error:
        raise ConfigError(f"invalid XML in '{path}': {error}")
    except OSError as error:
        raise ConfigError(f"cannot read config '{path}': {error}")

    root = tree.getroot()
    if root.tag != CONFIG_ROOT_TAG:
        raise ConfigError(
            f"root element must be <{CONFIG_ROOT_TAG}>, got <{root.tag}>"
        )
    return {
        "vfs": text_or_none(root, "vfs_path"),
        "script": text_or_none(root, "startup_script"),
    }


def first_set(primary, fallback):
    """Возвращает primary, если оно задано, иначе fallback."""
    return primary if primary is not None else fallback


def load_settings(argv=None):
    """Собирает итоговые настройки из командной строки и XML-файла.

    Значения из командной строки имеют приоритет над значениями из файла.
    Возвращает пару (settings, текст ошибки или None).
    """
    args = parse_args(argv)
    from_file = {"vfs": None, "script": None}
    error = None
    if args.config:
        try:
            from_file = read_xml_config(args.config)
        except ConfigError as config_error:
            error = str(config_error)

    settings = {
        "config": args.config,
        "vfs": first_set(args.vfs, from_file["vfs"]),
        "script": first_set(args.script, from_file["script"]),
    }
    return settings, error