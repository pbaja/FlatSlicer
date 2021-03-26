import sys, webbrowser
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from utils import Event
from .widgets import *
from .style import ICON_SETTINGS

class SettingsWindow:

    def __init__(self, root):
        self.root = root
        self.items = {}

        # Events
        self.octoprint_test_pressed = Event() 

        # Spawn window
        self.window = tk.Toplevel(self.root)
        self.window.title("Settings")
        self.window.geometry("600x400")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.iconphoto(False, tk.PhotoImage(file=ICON_SETTINGS))
        self.window.iconbitmap()
        self.close()

        # Add tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self._add_machine_tab()
        self._add_octoprint_tab()
        self._add_about_tab()

    def open(self):
        self.window.deiconify()
        self.window.grab_set()

    def close(self):
        self.window.withdraw()
        self.window.grab_release()

    def load_config(self, cfg):
        for path, item in self.items.items():
            value = cfg.get_value(path)
            if isinstance(item, tk.Entry):
                item.delete(0, tk.END)
                item.insert(0, str(value))
            elif isinstance(item, tk.Listbox):
                for x in value:
                    item.insert(tk.END, x)

    def dump_config(self, cfg):
        for path, item in self.items.items():
            if isinstance(item, tk.Entry):
                cfg.set_value(path, item.get())
            elif isinstance(item, tk.Listbox):
                cfg.set_value(path, list(item.get(0, item.size())))

    def _add_machine_tab(self):
        # Create frame
        frame = make_frame(self.notebook)
        self.notebook.add(frame, text='Machine')
        r = 0

        # Laser settings
        title_row(frame, r, 'Laser') ; r += 1
        self.items['machine.laser_on'] = entry_row(frame, r, 'Laser ON', desc='Used to turn on and set the laser power') ; r += 1
        self.items['machine.laser_off'] = entry_row(frame, r, 'Laser OFF', desc='Used to turn off the laser at the end') ; r += 1
        self.items['machine.min_power:float'] = entry_row(frame, r, 'Min Power [%]', desc='Minimum laser power used when travelling', validate=validate_float) ; r += 1
        
        # Global settings
        title_row(frame, r, 'Global') ; r += 1
        self.items['machine.burn_accel:float'] = entry_row(frame, r, 'Burn acceleration [mm/s²]', desc='Setting this too low will result in accidential gradients') ; r += 1
        self.items['machine.travel_accel:float'] = entry_row(frame, r, 'Travel acceleration [mm/s²]', desc='Acceleration for travelling') ; r += 1
        self.items['machine.travel_speed:float'] = entry_row(frame, r, 'Travel speed [mm/s]', desc='Speed used when not burning, can be set as high as your machine can handle.') ; r += 1


    def _add_octoprint_tab(self):
        # Create frame
        frame = make_frame(self.notebook)
        self.notebook.add(frame, text='OctoPrint')
        r = 0

        # Connection settings
        title_row(frame, r, 'Connection') ; r += 1
        self.items['octoprint.url'] = entry_row(frame, r, 'Hostname, IP or URL') ; r += 1
        self.items['octoprint.key'] = entry_row(frame, r, 'API Key') ; r += 1
        make_button(frame, r, 0, 'Test Connection', col_span=2, width=20, sticky=None, callback=self.octoprint_test_pressed) ; r += 1

    def _add_about_tab(self):
        # Create frame
        frame = make_frame(self.notebook)
        self.notebook.add(frame, text='About')
        r = 0

        # Information
        make_button(frame, r, 0, 'Visit GitHub', col_span=2, width=20, sticky=None, callback=lambda: webbrowser.open('https://github.com/pbaja/FlatSlicer'))


