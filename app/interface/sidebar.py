import tkinter as tk
from tkinter import ttk
from typing import List

from utils import Event
from .style import *
from .view import View


class SidebarView(View):
    def __init__(self, parent):
        super().__init__(parent)
        # Public
        self.items = {}
        self.addfile_pressed = Event()
        self.delfile_pressed = Event()
        self.trace_pressed = Event()
        self.generate_pressed = Event()
        self.export_pressed = Event()

    def init(self):
        box = SidebarListbox(self.frame, 'Files', 'files')
        box.add_button('Add file', callback=self.addfile_pressed)
        box.add_button('Remove', callback=self.delfile_pressed)
        self.items.update(box.items)

        widget = SidebarWidget(self.frame, 'Import')
        widget.add_entry('Image DPI', 'import.dpi:float')
        widget.add_entry('Epsilon [mm]', 'import.epsilon:float')
        self.items.update(widget.items)

        widget = SidebarWidget(self.frame, 'Global')
        widget.add_entry('Laser ON', 'global.laser_on')
        widget.add_entry('Laser OFF', 'global.laser_off')
        widget.add_entry('Min Power [%]', 'global.min_power:float', validate=self.validate_float)
        widget.add_entries('Offset [mm]', ['X', 'Y', 'Z'], ['global.offset.x:float', 'global.offset.y:float', 'global.offset.z:float'])
        widget.add_entry('Travel Speed [mm/s]', 'global.travel_speed:float', validate=self.validate_float)
        widget.add_entry('Bezier Resolution [mm]', 'global.bezier_resolution:float', validate=self.validate_float)
        widget.add_entry('Min Travel Distance [mm]', 'global.min_travel_distance:float', validate=self.validate_float)
        self.items.update(widget.items)

        widget = SidebarWidget(self.frame, 'Outline')
        widget.add_entry('Passes', 'outline.passes:int', validate=self.validate_int)
        widget.add_entry('Power [%]', 'outline.power:float', validate=self.validate_float)
        widget.add_entry('Speed [mm/s]', 'outline.speed:float', validate=self.validate_float)
        self.items.update(widget.items)

        widget = SidebarWidget(self.frame, 'Infill')
        widget.add_entry('Passes', 'infill.passes:int', validate=self.validate_int)
        widget.add_entry('Power [%]', 'infill.power:float', validate=self.validate_float)
        widget.add_entry('Speed [mm/s]', 'infill.speed:float', validate=self.validate_float)
        widget.add_entry('Line Spacing [mm]', 'infill.line_spacing:float', validate=self.validate_float)
        self.items.update(widget.items)

        buttons = SidebarButtons(self.frame, 'Output', 3)
        buttons.add_button('Trace bitmap', callback=self.trace_pressed)
        buttons.add_button('Generate Gcode', callback=self.generate_pressed)
        buttons.add_button('Export Gcode', callback=self.export_pressed)

    def validate_int(self, value:str) -> bool:
        try:
            if len(value) != 0: int(value) # Parseable to int
            return len(value) <= 1 or value[0] != '0' or value[0] != ' ' or value[-1] != ' '
        except:
            return False

    def validate_float(self, value:str) -> bool:
        try:
            if len(value) != 0: float(value) # Parseable to float
            return len(value) <= 1 or value[0] != '0' or value[0] != ' ' or value[-1] != ' '
        except:
            return False


class Widget:
    def __init__(self, parent, title_text, columnspan=2):
        self.items = {}
        # Add frame
        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.pack(fill=tk.BOTH)
        # Add title
        if title_text is not None:
            title_label = ttk.Label(self.frame, text=title_text, style='title.TLabel')
            title_label.columnconfigure(0, weight=1)
            title_label.grid(row=0, column=0, pady=5, columnspan=columnspan, sticky=tk.NSEW)

class SidebarWidget(Widget):
    def __init__(self, parent, title_text:str):
        super().__init__(parent, title_text)
        self.row = 0

    def add_label(self, label_text:str, row=-1):
        # Label
        label = ttk.Label(self.frame, text=label_text, anchor=tk.W)
        label.grid(row=self.row if row == -1 else row, column=0, padx=5, sticky=tk.NSEW)

    def add_entry(self, label_text:str, config_name:str, validate=None):
        self.row += 1
        self.add_label(label_text, self.row)
        entry = tk.Entry(self.frame, validate='all')
        entry.configure(relief='flat', background=COLOR_BG1)
        entry.columnconfigure(0, weight=1)
        entry.grid(row=self.row, column=1, padx=5, pady=2, sticky=tk.E)
        entry.insert(0, '-')
        if validate is not None:
            entry.config(validatecommand=(self.frame.register(validate), '%P'))
        self.items[config_name] = entry

    def add_entries(self, label_text:str, entry_label_texts:List[str], config_names:List[str], default_texts:List[str]=None, validate=None):
        self.row += 1
        self.add_label(label_text, self.row)
        # Add container frame
        frame = ttk.Frame(self.frame)
        frame.columnconfigure(0, weight=1)
        frame.grid(row=self.row, column=1, padx=5, sticky=tk.E)
        # Add buttons to this frame
        for col in range(len(entry_label_texts)):
            # Add label
            label = ttk.Label(frame, text=entry_label_texts[col], anchor=tk.W)
            label.columnconfigure(col*2, weight=0)
            label.grid(row=0, column=col*2, padx=5, sticky=tk.NSEW)
            # Add entry
            entry = tk.Entry(frame, width=4, validate='all')
            entry.configure(relief='flat', background=COLOR_BG1)
            entry.columnconfigure(col*2+1, weight=1)
            entry.grid(row=0, column=col*2+1, pady=5, columnspan=1, sticky=tk.NSEW)
            entry.insert(0, '-')
            if validate is not None:
                entry.config(validatecommand=(self.frame.register(validate), '%P'))
            self.items[config_names[col]] = entry

    # def add_button(self, button_text, callback=None):
    #     self.row += 1
    #     none_func = lambda: None
    #     btn = ttk.Button(self.frame, text=button_text, command=none_func if callback is None else callback)
    #     btn.columnconfigure(0, weight=1)
    #     btn.grid(row=self.row, column=0, pady=5, columnspan=2, sticky=tk.NSEW)

class SidebarButtons(Widget):
    def __init__(self, parent, title_text:str=None, columnspan:int=2):
        super().__init__(parent, title_text, columnspan)
        self.col = -1

    def add_button(self, button_text:str, callback=None):
        self.col += 1
        self.frame.columnconfigure(self.col, weight=1)
        none_func = lambda: None
        btn = ttk.Button(self.frame, text=button_text, width=5, command=none_func if callback is None else callback)
        btn.grid(row=1, column=self.col, pady=5, padx=2, columnspan=1, sticky=tk.NSEW)

class SidebarListbox(Widget):
    def __init__(self, parent, title_text:str, config_name:str):
        super().__init__(parent, title_text)
        self.button_frame = tk.Frame(self.frame)
        self.button_frame.grid(row=2, column=0, sticky=tk.NSEW)
        self.btn_col = -1
        # Add listbox
        box = tk.Listbox(self.frame, height=5, relief='flat', highlightthickness=0, background=COLOR_BG1)
        box.grid(row=1, column=0, sticky=tk.NSEW)
        self.items[config_name] = box

    def add_button(self, button_text:str, callback=None):
        self.btn_col += 1
        self.button_frame.columnconfigure(self.btn_col, weight=1)
        none_func = lambda: None
        btn = ttk.Button(self.button_frame, text=button_text, command=none_func if callback is None else callback)
        btn.grid(row=0, column=self.btn_col, pady=5, padx=2, sticky=tk.NSEW)