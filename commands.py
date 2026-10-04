import os
import shlex


class ShellError(Exception):
    """Ошибка выполнения команды"""


class ExitShell(Exception):
    """ользователь ввёл exit."""


def parse(line):
    line = os.path.expandvars(line)
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


def cmd_ls(args):
    return f"ls {args}"


def cmd_cd(args):
    if len(args) > 1:
        raise ShellError("cd: too many arguments")
    return f"cd {args}"


def cmd_exit(args):
    if args:
        raise ShellError("exit: too many arguments")
    raise ExitShell()


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
}


def execute(line):
    tokens = parse(line)
    if not tokens:
        return ""
    name, args = tokens[0], tokens[1:]
    handler = COMMANDS.get(name)
    if handler is None:
        raise ShellError(f"{name}: command not found")
    return handler(args)