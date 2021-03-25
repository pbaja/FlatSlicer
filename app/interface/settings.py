import tkinter as tk
from tkinter import ttk

class SettingsWindow:

    def __init__(self, root):
        self.root = root
        self.window = None

    def open(self):
        # Spawn window
        self.window = tk.Toplevel(self.root)
        self.window.title("Settings")
        self.window.geometry("400x300")
        self.window.grab_set()

        # Add tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self._add_machine_tab()
        self._add_octoprint_tab()

    def _add_machine_tab(self):
        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text='Machine')

    def _add_octoprint_tab(self):
        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text='OctoPrint')