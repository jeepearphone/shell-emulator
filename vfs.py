import os
import shutil


class VFSError(Exception):
    """Ошибка работы с VFS: не удалось загрузить или очистить."""


def why_unsafe_to_clear(path):
    """Причина, по которой папку нельзя очищать на диске, или None, если можно."""
    path = os.path.normcase(os.path.abspath(path))
    program = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
    home = os.path.normcase(os.path.abspath(os.path.expanduser("~")))

    if os.path.dirname(path) == path:
        return "it is a drive root"
    if path == home:
        return "it is the home directory"
    if program == path or program.startswith(path + os.sep):
        return "it contains the emulator itself"
    return None


class VFS:
    """Виртуальная файловая система: дерево папок и файлов в памяти.

    Папка -> словарь {имя: содержимое}
    Файл  -> bytes (байты файла, как они лежат на диске)
    """

    def __init__(self):
        self.name = "default"  # имя VFS для заголовка окна
        self.source = None     # путь к папке на диске; None = VFS по умолчанию
        self.root = {}         # корневая папка; пустой словарь = пустая VFS


    def load(self, path):
        if not os.path.exists(path):
            raise VFSError(f"VFS not found: {path}")
        if not os.path.isdir(path):
            raise VFSError(f"invalid VFS format: '{path}' is not a directory")
        try:
            tree = self._read_dir(path)
        except OSError as e:
            raise VFSError(f"cannot read VFS '{path}': {e}")

        self.root = tree
        self.source = os.path.abspath(path)
        self.name = os.path.basename(self.source) or self.source

    def _read_dir(self, path):
        node = {}
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if os.path.islink(full):
                continue  # ссылки пропускаем, чтобы не ходить по кругу
            if os.path.isdir(full):
                node[name] = self._read_dir(full)
            else:
                with open(full, "rb") as f:
                    node[name] = f.read()
        return node



    def init_default(self):
        """Заменяет VFS на VFS по умолчанию (пустую) и очищает папку на диске."""
        if self.source is not None:
            self._clear_physical()
        self.root = {}

    def _clear_physical(self):
        """Удаляет всё содержимое папки-источника. Сама папка остаётся."""
        reason = why_unsafe_to_clear(self.source)
        if reason:
            raise VFSError(f"refusing to clear '{self.source}': {reason}")
        if not os.path.isdir(self.source):
            return  # папки уже нет, очищать нечего
        try:
            for name in os.listdir(self.source):
                full = os.path.join(self.source, name)
                if os.path.isdir(full) and not os.path.islink(full):
                    shutil.rmtree(full)
                else:
                    os.remove(full)
        except OSError as e:
            raise VFSError(f"cannot clear '{self.source}': {e}")

    # ---------- поиск по пути ----------

    def get_node(self, parts):
        """Спускается от корня по списку имён и возвращает то, что там лежит."""
        node = self.root
        for name in parts:
            node = node[name]
        return node

    def resolve(self, path, cwd):
        """Ищет файл или папку по пути"""
        if path.startswith("/"):
            parts = []
        else:
            parts = list(cwd)  # относительный путь

        for piece in path.split("/"):
            if piece == "" or piece == ".":
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

    # ---------- изменение (только в памяти) ----------

    def remove(self, parts):
        parent = self.get_node(parts[:-1])
        del parent[parts[-1]]

    # ---------- информация ----------

    def count(self, node=None):
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
        if node is None:
            node = self.root
        lines = []
        for name in sorted(node):
            child = node[name]
            if isinstance(child, dict):
                lines.append("  " * indent + name + "/")
                lines.extend(self.tree_lines(child, indent + 1))
            else:
                lines.append("  " * indent + f"{name} ({len(child)} bytes)")
        return lines