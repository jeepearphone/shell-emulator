"""Разбор командной строки и команды эмулятора."""

import os
import shlex

from vfs import VFSError

QUOTE_CHARS = "\"'"
MIN_QUOTED_LEN = 2
MAX_LS_PATHS = 1
MAX_CD_ARGS = 1
RM_RECURSIVE_FLAGS = "rR"
RM_FORCE_FLAG = "f"
LS_LONG_FLAG = "l"


class ShellError(Exception):
    """Ошибка выполнения команды, её текст выводится пользователю."""


class ExitShell(Exception):
    """Сигнал о том, что пользователь ввёл exit."""


class Session:
    """Состояние эмулятора, с которым работают команды.

    vfs     -- загруженная VFS;
    confirm -- функция, которая задаёт вопрос и возвращает True или False;
    cwd     -- текущая папка в виде списка имён, [] означает корень.
    """

    def __init__(self, vfs, confirm):
        """Создаёт сессию с текущей папкой в корне VFS."""
        self.vfs = vfs
        self.confirm = confirm
        self.cwd = []

    def cwd_path(self):
        """Возвращает текущую папку в виде строки, например /home/user."""
        return "/" + "/".join(self.cwd)


def strip_quotes(token):
    """Убирает парные кавычки вокруг слова."""
    quoted = (
        len(token) >= MIN_QUOTED_LEN
        and token[0] == token[-1]
        and token[0] in QUOTE_CHARS
    )
    return token[1:-1] if quoted else token


def parse(line):
    """Раскрывает переменные окружения ОС и делит строку на слова."""
    line = os.path.expandvars(line)
    try:
        tokens = shlex.split(line, posix=False)
    except ValueError as error:
        raise ShellError(f"parse error: {error}")
    return [strip_quotes(token) for token in tokens]


def is_option(arg):
    """Проверяет, является ли аргумент набором флагов вида -abc."""
    return arg.startswith("-") and arg != "-"


def split_options(command, args, allowed):
    """Отделяет флаги от остальных аргументов.

    Возвращает пару (множество букв флагов, список прочих аргументов).
    Неизвестный флаг вызывает ShellError.
    """
    flags = set()
    rest = []
    for arg in args:
        if not is_option(arg):
            rest.append(arg)
            continue
        for letter in arg[1:]:
            if letter not in allowed:
                raise ShellError(
                    f"{command}: invalid option -- '{letter}'"
                )
            flags.add(letter)
    return flags, rest


def format_entry(name, node, long_format):
    """Форматирует одну запись для вывода ls."""
    is_dir = isinstance(node, dict)
    shown = name + "/" if is_dir else name
    if not long_format:
        return shown
    kind = "d" if is_dir else "-"
    size = "-" if is_dir else len(node)
    return f"{kind} {size:>8}  {shown}"


def cmd_ls(args, session):
    """Выводит содержимое папки или имя файла; с -l тип и размер."""
    flags, paths = split_options("ls", args, LS_LONG_FLAG)
    long_format = LS_LONG_FLAG in flags
    if len(paths) > MAX_LS_PATHS:
        raise ShellError("ls: too many arguments")

    path = paths[0] if paths else "."
    try:
        _, node = session.vfs.resolve(path, session.cwd)
    except VFSError as error:
        raise ShellError(f"ls: cannot access '{path}': {error}")

    if isinstance(node, dict):
        entries = [(name, node[name]) for name in sorted(node)]
    else:
        entries = [(path, node)]
    lines = [format_entry(name, child, long_format)
             for name, child in entries]
    separator = "\n" if long_format else "  "
    return separator.join(lines)


def cmd_cd(args, session):
    """Переходит в папку; без аргумента переходит в корень VFS."""
    if len(args) > MAX_CD_ARGS:
        raise ShellError("cd: too many arguments")
    path = args[0] if args else "/"
    try:
        parts, node = session.vfs.resolve(path, session.cwd)
    except VFSError as error:
        raise ShellError(f"cd: {path}: {error}")
    if not isinstance(node, dict):
        raise ShellError(f"cd: {path}: Not a directory")
    session.cwd = parts
    return ""


def cmd_pwd(args, session):
    """Выводит путь к текущей папке."""
    if args:
        raise ShellError("pwd: too many arguments")
    return session.cwd_path()


def read_file(path, session):
    """Возвращает текст файла VFS для команды cat."""
    try:
        _, node = session.vfs.resolve(path, session.cwd)
    except VFSError as error:
        raise ShellError(f"cat: {path}: {error}")
    if isinstance(node, dict):
        raise ShellError(f"cat: {path}: Is a directory")
    return node.decode("utf-8", errors="replace")


def cmd_cat(args, session):
    """Выводит содержимое одного или нескольких файлов."""
    if not args:
        raise ShellError("cat: missing file operand")
    text = "".join(read_file(path, session) for path in args)
    text = text.replace("\r\n", "\n")
    return text.removesuffix("\n")


def rm_target(path, session, recursive):
    """Возвращает части пути, который можно удалить командой rm.

    Если пути нет, бросает VFSError; если удалять нельзя, ShellError.
    """
    parts, node = session.vfs.resolve(path, session.cwd)
    prefix = f"rm: cannot remove '{path}'"
    if not parts:
        raise ShellError(f"{prefix}: it is the root directory")
    if session.cwd[:len(parts)] == parts:
        raise ShellError(
            f"{prefix}: it is the current directory or its parent"
        )
    if isinstance(node, dict) and not recursive:
        raise ShellError(f"{prefix}: Is a directory")
    return parts


def cmd_rm(args, session):
    """Удаляет файлы и папки только в памяти VFS.

    -r или -R разрешает удалять папки вместе с содержимым,
    -f не сообщает об отсутствующих файлах.
    """
    allowed = RM_RECURSIVE_FLAGS + RM_FORCE_FLAG
    flags, paths = split_options("rm", args, allowed)
    recursive = bool(flags & set(RM_RECURSIVE_FLAGS))
    force = RM_FORCE_FLAG in flags
    if not paths and not force:
        raise ShellError("rm: missing operand")

    errors = []
    for path in paths:
        try:
            session.vfs.remove(rm_target(path, session, recursive))
        except VFSError as error:
            if not force:
                errors.append(f"rm: cannot remove '{path}': {error}")
        except ShellError as error:
            errors.append(str(error))
    if errors:
        raise ShellError("\n".join(errors))
    return ""


def cmd_exit(args, session):
    """Завершает работу эмулятора."""
    if args:
        raise ShellError("exit: too many arguments")
    raise ExitShell()


def cmd_vfs_info(args, session):
    """Выводит имя VFS, путь к источнику и дерево содержимого."""
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
    except VFSError as error:
        raise ShellError(f"vfs-init: {error}")
    session.cwd = []

    message = "VFS replaced with default (empty) VFS"
    if vfs.source is not None:
        message += f", directory cleared: {vfs.source}"
    return message


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "pwd": cmd_pwd,
    "cat": cmd_cat,
    "rm": cmd_rm,
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
    "vfs-init": cmd_vfs_init,
}


def execute(line, session):
    """Выполняет одну строку и возвращает текст вывода.

    При ошибке бросает ShellError, при команде exit бросает ExitShell.
    """
    tokens = parse(line)
    if not tokens:
        return ""
    name, args = tokens[0], tokens[1:]
    handler = COMMANDS.get(name)
    if handler is None:
        raise ShellError(f"{name}: command not found")
    return handler(args, session)