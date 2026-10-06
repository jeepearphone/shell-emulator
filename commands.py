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


def cmd_ls(args, session):
    return f"ls {args}"


def cmd_cd(args, session):
    if len(args) > 1:
        raise ShellError("cd: too many arguments")
    return f"cd {args}"


def cmd_exit(args, session):
    if args:
        raise ShellError("exit: too many arguments")
    raise ExitShell()


def cmd_vfs_info(args, session):
    """показывает, что сейчас лежит в VFS."""
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

    if vfs.source is not None:
        return f"VFS replaced with default (empty) VFS, directory cleared: {vfs.source}"
    return "VFS replaced with default (empty) VFS"


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
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