import tkinter as tk

from commands import execute, ShellError, ExitShell


class ShellGUI:
    def __init__(self, vfs_name):
        self.vfs_name = vfs_name

        self.root = tk.Tk()
        self.root.title(f"Эмулятор - [{vfs_name}]")
        self.root.geometry("800x500")

        self.output = tk.Text(
            self.root, state="disabled", wrap="word",
            bg="black", fg="#dddddd", font=("Consolas", 12),
        )
        self.output.tag_config("prompt", foreground="#6bff6b")
        self.output.tag_config("error", foreground="#ff6b6b")
        self.output.pack(fill="both", expand=True)

        self.entry = tk.Entry(
            self.root, font=("Consolas", 12),
            bg="#222222", fg="white", insertbackground="white",
        )
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus()

    def print(self, text, tag=None):
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n", tag)
        self.output.config(state="disabled")
        self.output.see(tk.END)

    def on_enter(self, event):
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.print(f"{self.vfs_name}$ {line}", "prompt")
        try:
            result = execute(line)
            if result:
                self.print(result)
        except ShellError as e:
            self.print(f"Error: {e}", "error")
        except ExitShell:
            self.root.destroy()

    def run(self):
        self.root.mainloop()