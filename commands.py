import os
import shlex

from vfs import VFSError


class ShellError(Exception):
    """Ошибка выполнения команды, её текст покажем пользователю."""


class ExitShell(Exception):
    """Сигнал: пользователь ввёл exit."""


class Session:
    """Состояние эмулятора, с которым работают команды."""

    def __init__(self, vfs, confirm):
        self.vfs = vfs          # загруженная VFS
        self.confirm = confirm  # функция: текст вопроса -> True (да) / False (нет)
        self.cwd = []           # текущая папка: [] = корень, ['home', 'user'] = /home/user

    def cwd_path(self):
        return "/" + "/".join(self.cwd)


def parse(line):
    """Раскрывает переменные окружения и режет строку на слова."""
    line = os.path.expandvars(line)  # $HOME -> реальный путь
    try:
        tokens = shlex.split(line, posix=False)
    except ValueError as e:
        raise ShellError(f"parse error: {e}")

    result = []
    for t in tokens:
        if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
            t = t[1:-1]
        result.append(t)
    return result


def format_entry(name, node, long_format):
    is_dir = isinstance(node, dict)
    shown = name + "/" if is_dir else name
    if not long_format:
        return shown
    kind = "d" if is_dir else "-"
    size = "-" if is_dir else len(node)
    return f"{kind} {size:>8}  {shown}"


def cmd_ls(args, session):
    long_format = False
    paths = []
    for arg in args:
        if arg.startswith("-") and len(arg) > 1:
            for letter in arg[1:]:
                if letter != "l":
                    raise ShellError(f"ls: invalid option -- '{letter}'")
            long_format = True
        else:
            paths.append(arg)
    if len(paths) > 1:
        raise ShellError("ls: too many arguments")

    path = paths[0] if paths else "."
    try:
        parts, node = session.vfs.resolve(path, session.cwd)
    except VFSError as e:
        raise ShellError(f"ls: cannot access '{path}': {e}")

    if isinstance(node, dict):
        entries = [(name, node[name]) for name in sorted(node)]
    else:
        entries = [(path, node)]

    lines = [format_entry(name, child, long_format) for name, child in entries]
    if long_format:
        return "\n".join(lines)
    return "  ".join(lines)


def cmd_cd(args, session):
    if len(args) > 1:
        raise ShellError("cd: too many arguments")
    path = args[0] if args else "/"
    try:
        parts, node = session.vfs.resolve(path, session.cwd)
    except VFSError as e:
        raise ShellError(f"cd: {path}: {e}")
    if not isinstance(node, dict):
        raise ShellError(f"cd: {path}: Not a directory")
    session.cwd = parts
    return ""


def cmd_pwd(args, session):
    if args:
        raise ShellError("pwd: too many arguments")
    return session.cwd_path()


def cmd_cat(args, session):
    if not args:
        raise ShellError("cat: missing file operand")
    chunks = []
    for path in args:
        try:
            parts, node = session.vfs.resolve(path, session.cwd)
        except VFSError as e:
            raise ShellError(f"cat: {path}: {e}")
        if isinstance(node, dict):
            raise ShellError(f"cat: {path}: Is a directory")
        chunks.append(node.decode("utf-8", errors="replace"))

    text = "".join(chunks).replace("\r\n", "\n")
    if text.endswith("\n"):
        text = text[:-1]  # окно само добавит перенос строки в конце
    return text


def cmd_exit(args, session):
    if args:
        raise ShellError("exit: too many arguments")
    raise ExitShell()


def cmd_vfs_info(args, session):
    if args:
        raise ShellError("vfs-info: too many arguments")
    vfs = session.vfs
    dirs, files = vfs.count()
    lines = [
        f"name:   {vfs.name}",
        f"source: {vfs.source or '(none)'}",
        f"size:   {dirs} directories, {files} files",
        "/",
    ]
    lines += vfs.tree_lines(indent=1)
    return "\n".join(lines)


def cmd_vfs_init(args, session):
    """Заменяет VFS на VFS по умолчанию и очищает папку на диске."""
    if args:
        raise ShellError("vfs-init: too many arguments")
    vfs = session.vfs

    if vfs.source is not None:
        question = (
            "vfs-init удалит ВСЁ содержимое папки на диске:\n\n"
            f"{vfs.source}\n\nПродолжить?"
        )
        if not session.confirm(question):
            return "vfs-init: cancelled, nothing changed"

    try:
        vfs.init_default()
    except VFSError as e:
        raise ShellError(f"vfs-init: {e}")
    session.cwd = []  # старой папки больше нет, возвращаемся в корень

    if vfs.source is not None:
        return f"VFS replaced with default (empty) VFS, directory cleared: {vfs.source}"
    return "VFS replaced with default (empty) VFS"


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "pwd": cmd_pwd,
    "cat": cmd_cat,
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
    "vfs-init": cmd_vfs_init,
}


def execute(line, session):
    """Выполняет одну строку. Возвращает текст вывода или бросает ShellError."""
    tokens = parse(line)
    if not tokens:
        return ""
    name, args = tokens[0], tokens[1:]
    handler = COMMANDS.get(name)
    if handler is None:
        raise ShellError(f"{name}: command not found")
    return handler(args, session)