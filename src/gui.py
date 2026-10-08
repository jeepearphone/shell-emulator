"""Графическое окно эмулятора на Tkinter."""

import tkinter as tk
from tkinter import messagebox

from commands import execute, Session, ShellError, ExitShell
from vfs import VFS, VFSError

WINDOW_SIZE = "800x500"
FONT = ("Consolas", 12)
SCRIPT_DELAY_MS = 100
STATUS_OK = "ok"
STATUS_ERROR = "error"
STATUS_EXIT = "exit"
TAG_COLORS = {
    "prompt": "#6bff6b",
    "error": "#ff6b6b",
    "debug": "#6bb5ff",
}


def load_vfs(path):
    """Загружает VFS из папки.

    Возвращает пару (VFS, текст ошибки или None). При ошибке остаётся
    пустая VFS по умолчанию.
    """
    vfs = VFS()
    if not path:
        return vfs, None
    try:
        vfs.load(path)
    except VFSError as error:
        return vfs, str(error)
    return vfs, None


def read_script(path):
    """Читает стартовый скрипт и возвращает список его строк."""
    with open(path, encoding="utf-8-sig") as file:
        return file.read().splitlines()


def is_skipped(line):
    """Проверяет, что строка скрипта пустая или является комментарием."""
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


class ShellGUI:
    """Окно эмулятора: поле вывода и строка ввода команд."""

    def __init__(self, settings, config_error=None):
        """Загружает VFS, создаёт окно и выводит отладочную информацию."""
        self.settings = settings
        self.vfs, vfs_error = load_vfs(settings["vfs"])
        self.session = Session(self.vfs, self.confirm)

        self.root = tk.Tk()
        self.root.title(f"Эмулятор - [{self.vfs.name}]")
        self.root.geometry(WINDOW_SIZE)
        self.output = self.create_output()
        self.entry = self.create_entry()

        self.show_debug()
        if config_error:
            self.print(f"Error: {config_error}", "error")
        self.show_vfs_status(vfs_error)
        if settings["script"]:
            self.root.after(
                SCRIPT_DELAY_MS, self.run_script, settings["script"]
            )

    def create_output(self):
        """Создаёт поле вывода с цветами для приглашения и ошибок."""
        output = tk.Text(
            self.root, state="disabled", wrap="word",
            bg="black", fg="#dddddd", font=FONT,
        )
        for tag, color in TAG_COLORS.items():
            output.tag_config(tag, foreground=color)
        output.pack(fill="both", expand=True)
        return output

    def create_entry(self):
        """Создаёт строку ввода команд."""
        entry = tk.Entry(
            self.root, font=FONT,
            bg="#222222", fg="white", insertbackground="white",
        )
        entry.pack(fill="x")
        entry.bind("<Return>", self.on_enter)
        entry.focus()
        return entry

    def confirm(self, question):
        """Показывает окно подтверждения и возвращает ответ пользователя."""
        return messagebox.askyesno(
            "Подтверждение", question,
            parent=self.root, icon="warning", default="no",
        )

    def print(self, text, tag=None):
        """Добавляет строку в поле вывода."""
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n", tag)
        self.output.config(state="disabled")
        self.output.see(tk.END)

    def show_debug(self):
        """Выводит значения всех параметров при запуске."""
        self.print("[debug] startup parameters:", "debug")
        for key in ("config", "vfs", "script"):
            value = self.settings[key]
            shown = value if value is not None else "(not set)"
            self.print(f"[debug]   {key} = {shown}", "debug")

    def show_vfs_status(self, vfs_error):
        """Сообщает об ошибке загрузки VFS или о её размере."""
        if vfs_error:
            self.print(f"Error: {vfs_error}", "error")
            self.print("[debug] using default (empty) VFS", "debug")
            return
        dirs, files = self.vfs.count()
        self.print(
            f"[debug] VFS '{self.vfs.name}' in memory: "
            f"{dirs} directories, {files} files", "debug",
        )

    def run_line(self, line):
        """Выполняет одну команду и выводит ввод и результат."""
        prompt = f"{self.vfs.name}:{self.session.cwd_path()}$ "
        self.print(prompt + line, "prompt")
        try:
            result = execute(line, self.session)
        except ShellError as error:
            self.print(f"Error: {error}", "error")
            return STATUS_ERROR
        except ExitShell:
            return STATUS_EXIT
        if result:
            self.print(result)
        return STATUS_OK

    def run_script(self, path):
        """Выполняет стартовый скрипт, пропуская ошибочные строки."""
        try:
            lines = read_script(path)
        except (OSError, UnicodeDecodeError) as error:
            self.print(
                f"Error: cannot read startup script '{path}': {error}",
                "error",
            )
            return

        self.print(f"--- startup script: {path} ---", "debug")
        for number, line in enumerate(lines, start=1):
            if is_skipped(line):
                continue
            status = self.run_line(line)
            if status == STATUS_ERROR:
                self.print(f"Script error: line {number} skipped", "error")
            elif status == STATUS_EXIT:
                self.root.destroy()
                return
        self.print("--- script finished ---", "debug")

    def on_enter(self, event):
        """Обрабатывает нажатие Enter в строке ввода."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        if self.run_line(line) == STATUS_EXIT:
            self.root.destroy()

    def run(self):
        """Запускает главный цикл окна."""
        self.root.mainloop()