"""Общие функции для тестов: создание тестовой VFS на диске."""

import os
import tempfile

SAMPLE_FILES = {
    "readme.txt": "root readme\n",
    "etc/config.txt": "mode=test\n",
    "home/user/notes.txt": "my notes\n",
    "home/user/docs/report.txt": "report text\n",
    "home/user/docs/todo.txt": "todo list\n",
}


def make_sample_dir():
    """Создаёт временную папку с деревом файлов в 4 уровня.

    Возвращает объект TemporaryDirectory; путь лежит в атрибуте name.
    """
    temp = tempfile.TemporaryDirectory()
    base = os.path.join(temp.name, "deep")
    for relative, text in SAMPLE_FILES.items():
        full = os.path.join(base, *relative.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as file:
            file.write(text)
    return temp


def sample_path(temp):
    """Возвращает путь к папке deep внутри временной папки."""
    return os.path.join(temp.name, "deep")