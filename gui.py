import os
import tkinter as tk

from commands import execute, ShellError, ExitShell


class ShellGUI:
    def __init__(self, settings, config_error=None):
        self.settings = settings
        if settings["vfs"]:
            self.vfs_name = os.path.basename(os.path.normpath(settings["vfs"]))
        else:
            self.vfs_name = "no-vfs"

        self.root = tk.Tk()
        self.root.title(f"Эмулятор - [{self.vfs_name}]")
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
        if settings["script"]:
            self.root.after(100, self.run_script, settings["script"])

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
        """Выполняет строку и показывает ввод и вывод. Возвращает 'ok', 'error' или 'exit'."""
        self.print(f"{self.vfs_name}$ {line}", "prompt")
        try:
            result = execute(line)
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