"""Виртуальная файловая система (VFS), которая хранится в памяти."""

import os
import shutil


class VFSError(Exception):
    """Ошибка работы с VFS: не удалось загрузить или очистить."""


def project_root():
    """Возвращает путь к корню проекта (папка над src)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def why_unsafe_to_clear(path):
    """Возвращает причину, по которой папку нельзя очищать, или None."""
    path = os.path.normcase(os.path.abspath(path))
    program = os.path.normcase(project_root())
    home = os.path.normcase(os.path.abspath(os.path.expanduser("~")))

    if os.path.dirname(path) == path:
        return "it is a drive root"
    if path == home:
        return "it is the home directory"
    if program == path or program.startswith(path + os.sep):
        return "it contains the emulator itself"
    return None


def read_dir(path):
    """Читает папку с диска и возвращает её дерево в виде словаря.

    Папка превращается в словарь {имя: содержимое}, файл в bytes.
    Символические ссылки пропускаются, чтобы не уйти в цикл.
    """
    node = {}
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        if os.path.islink(full):
            continue
        if os.path.isdir(full):
            node[name] = read_dir(full)
        else:
            with open(full, "rb") as file:
                node[name] = file.read()
    return node


def clear_dir(path):
    """Удаляет всё содержимое папки на диске, саму папку оставляет."""
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if os.path.isdir(full) and not os.path.islink(full):
            shutil.rmtree(full)
        else:
            os.remove(full)


class VFS:
    """Дерево папок и файлов в памяти.

    Папка хранится как словарь {имя: содержимое}, файл как bytes.
    Атрибут source хранит путь к папке-источнику на диске или None
    для VFS по умолчанию.
    """

    def __init__(self):
        """Создаёт пустую VFS по умолчанию."""
        self.name = "default"
        self.source = None
        self.root = {}

    def load(self, path):
        """Загружает VFS в память из папки на диске."""
        if not os.path.exists(path):
            raise VFSError(f"VFS not found: {path}")
        if not os.path.isdir(path):
            raise VFSError(
                f"invalid VFS format: '{path}' is not a directory"
            )
        try:
            tree = read_dir(path)
        except OSError as error:
            raise VFSError(f"cannot read VFS '{path}': {error}")

        self.root = tree
        self.source = os.path.abspath(path)
        self.name = os.path.basename(self.source) or self.source

    def init_default(self):
        """Заменяет VFS на пустую и очищает папку-источник на диске."""
        if self.source is not None:
            self.clear_physical()
        self.root = {}

    def clear_physical(self):
        """Очищает папку-источник на диске, если это безопасно."""
        reason = why_unsafe_to_clear(self.source)
        if reason:
            raise VFSError(f"refusing to clear '{self.source}': {reason}")
        if not os.path.isdir(self.source):
            return
        try:
            clear_dir(self.source)
        except OSError as error:
            raise VFSError(f"cannot clear '{self.source}': {error}")

    def get_node(self, parts):
        """Спускается от корня по списку имён и возвращает узел."""
        node = self.root
        for name in parts:
            node = node[name]
        return node

    def resolve(self, path, cwd):
        """Находит файл или папку по пути.

        Путь может быть абсолютным или относительным текущей папки cwd,
        поддерживаются "." и "..". Возвращает пару (список имён, узел).
        """
        parts = [] if path.startswith("/") else list(cwd)
        for piece in path.split("/"):
            if piece in ("", "."):
                continue
            node = self.get_node(parts)
            if not isinstance(node, dict):
                raise VFSError("Not a directory")
            if piece == "..":
                if parts:
                    parts.pop()
            elif piece in node:
                parts.append(piece)
            else:
                raise VFSError("No such file or directory")
        return parts, self.get_node(parts)

    def remove(self, parts):
        """Удаляет файл или папку только из памяти."""
        parent = self.get_node(parts[:-1])
        del parent[parts[-1]]

    def count(self, node=None):
        """Считает папки и файлы. Возвращает пару (папки, файлы)."""
        if node is None:
            node = self.root
        dirs, files = 0, 0
        for child in node.values():
            if isinstance(child, dict):
                sub_dirs, sub_files = self.count(child)
                dirs += 1 + sub_dirs
                files += sub_files
            else:
                files += 1
        return dirs, files

    def tree_lines(self, node=None, indent=0):
        """Возвращает строки дерева VFS с отступами для vfs-info."""
        if node is None:
            node = self.root
        lines = []
        for name in sorted(node):
            child = node[name]
            prefix = "  " * indent
            if isinstance(child, dict):
                lines.append(f"{prefix}{name}/")
                lines.extend(self.tree_lines(child, indent + 1))
            else:
                lines.append(f"{prefix}{name} ({len(child)} bytes)")
        return lines