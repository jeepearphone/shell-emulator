import tkinter as tk
from tkinter import messagebox

from commands import execute, Session, ShellError, ExitShell
from vfs import VFS, VFSError


class ShellGUI:
    def __init__(self, settings, config_error=None):
        self.settings = settings

        # загружаем VFS в память; если не вышло, остаёмся с VFS по умолчанию
        self.vfs = VFS()
        vfs_error = None
        if settings["vfs"]:
            try:
                self.vfs.load(settings["vfs"])
            except VFSError as e:
                vfs_error = str(e)
        self.session = Session(self.vfs, self.confirm)

        self.root = tk.Tk()
        self.root.title(f"Эмулятор - [{self.vfs.name}]")  # имя VFS в заголовке
        self.root.geometry("800x500")

        self.output = tk.Text(
            self.root, state="disabled", wrap="word",
            bg="black", fg="#dddddd", font=("Consolas", 12),
        )
        self.output.tag_config("prompt", foreground="#6bff6b")
        self.output.tag_config("error", foreground="#ff6b6b")
        self.output.tag_config("debug", foreground="#6bb5ff")
        self.output.pack(fill="both", expand=True)

        self.entry = tk.Entry(
            self.root, font=("Consolas", 12),
            bg="#222222", fg="white", insertbackground="white",
        )
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus()

        self.show_debug()
        if config_error:
            self.print(f"Error: {config_error}", "error")
        if vfs_error:
            self.print(f"Error: {vfs_error}", "error")
            self.print("[debug] using default (empty) VFS", "debug")
        else:
            dirs, files = self.vfs.count()
            self.print(
                f"[debug] VFS '{self.vfs.name}' in memory: "
                f"{dirs} directories, {files} files", "debug",
            )
        if settings["script"]:
            self.root.after(100, self.run_script, settings["script"])

    def confirm(self, question):
        return messagebox.askyesno(
            "Подтверждение", question,
            parent=self.root, icon="warning", default="no",
        )

    def print(self, text, tag=None):
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n", tag)
        self.output.config(state="disabled")
        self.output.see(tk.END)

    def show_debug(self):
        """Отладочный вывод всех параметров при запуске."""
        self.print("[debug] startup parameters:", "debug")
        for key in ("config", "vfs", "script"):
            value = self.settings[key]
            shown = value if value is not None else "(not set)"
            self.print(f"[debug]   {key} = {shown}", "debug")

    def run_line(self, line):
        self.print(f"{self.vfs.name}:{self.session.cwd_path()}$ {line}", "prompt")
        try:
            result = execute(line, self.session)
            if result:
                self.print(result)
            return "ok"
        except ShellError as e:
            self.print(f"Error: {e}", "error")
            return "error"
        except ExitShell:
            return "exit"

    def run_script(self, path):
        try:
            with open(path, encoding="utf-8-sig") as f:
                lines = f.read().splitlines()
        except (OSError, UnicodeDecodeError) as e:
            self.print(f"Error: cannot read startup script '{path}': {e}", "error")
            return

        self.print(f"--- startup script: {path} ---", "debug")
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue  # пустые строки и комментарии пропускаем
            status = self.run_line(line)
            if status == "error":
                self.print(f"Script error: line {number} skipped", "error")
            elif status == "exit":
                self.root.destroy()
                return
        self.print("--- script finished ---", "debug")

    def on_enter(self, event):
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        if self.run_line(line) == "exit":
            self.root.destroy()

    def run(self):
        self.root.mainloop()