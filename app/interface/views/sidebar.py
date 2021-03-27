import tkinter as tk
from tkinter import ttk
from typing import List

from ...utils import Event
from ..style import *
from ..widgets import *
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
        self.settings_pressed = Event()

    def init(self):
        header = SidebarHeader(self.frame)
        header.add_title('FlatSlicer')
        header.add_button('Settings', callback=self.settings_pressed)

        box = SidebarListbox(self.frame, 'Files', 'files')
        box.add_button('Add file', callback=self.addfile_pressed)
        box.add_button('Remove', callback=self.delfile_pressed)
        self.items.update(box.items)

        widget = SidebarWidget(self.frame, 'Import')
        widget.add_entry('Image DPI', 'image.dpi:float')
        widget.add_entries('Offset [mm]', ['X', 'Y', 'Z'], ['image.offset.x:float', 'image.offset.y:float', 'image.offset.z:float'])
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
        buttons.add_button('Trace image', callback=self.trace_pressed)
        buttons.add_button('Generate Gcode', callback=self.generate_pressed)
        buttons.add_button('Export Gcode', callback=self.export_pressed)

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
    def __init__(self, parent, title_text, columnspan=2, style='TFrame'):
        self.items = {}
        # Add frame
        self.frame = ttk.Frame(parent, style=style)
        self.frame.columnconfigure(0, weight=1)
        self.frame.pack(fill=tk.BOTH)
        # Add title
        if title_text is not None:
            title_label = ttk.Label(self.frame, text=title_text, anchor=tk.W,style='title.TLabel')
            title_label.columnconfigure(0, weight=1)
            title_label.grid(row=0, column=0, pady=5, padx=5, columnspan=columnspan, sticky=tk.NSEW)

class SidebarWidget(Widget):
    def __init__(self, parent, title_text:str):
        super().__init__(parent, title_text)
        self.row = 0

    def add_label(self, label_text:str, row=-1):
        # Label
        label = ttk.Label(self.frame, text=label_text, anchor=tk.W)
        label.grid(row=self.row if row == -1 else row, column=0, padx=(15, 5), sticky=tk.NSEW)

    def add_entry(self, label_text:str, config_name:str, validate=None):
        self.row += 1
        self.items[config_name] = make_entry(self.frame, self.row, 1, validate=validate)
        make_label(self.frame, self.row, 0, label_text, pad_x=(15,5))

    def add_entries(self, label_text:str, entry_label_texts:List[str], config_names:List[str], default_texts:List[str]=None, validate=None):
        self.row += 1
        make_label(self.frame, self.row, 0, label_text, pad_x=(15,5))
        # Add container frame
        frame = ttk.Frame(self.frame)
        frame.columnconfigure(0, weight=1)
        frame.grid(row=self.row, column=1, padx=5, sticky=tk.E)
        # Add buttons to this frame
        for col in range(len(entry_label_texts)):
            make_label(frame, 0, col*2, entry_label_texts[col], col_weight=0)
            self.items[config_names[col]] = make_entry(frame, 0, col*2+1, validate=validate, width=4)

class SidebarHeader(Widget):
    def __init__(self, parent, columnspan:int=2):
        super().__init__(parent, None, columnspan, style='header.TFrame')
        self.col = -1

    def add_title(self, label_text:str):
        self.col += 1
        self.frame.columnconfigure(self.col, weight=1)
        label = ttk.Label(self.frame, text=label_text, anchor=tk.W, style='header.TLabel')
        label.grid(row=0, column=self.col, padx=5, sticky=tk.NSEW)

    def add_button(self, button_text:str, callback=None):
        self.col += 1
        none_func = lambda: None
        btn = ttk.Button(self.frame, text=button_text, width=len(button_text), command=none_func if callback is None else callback, style='header.TButton')
        btn.grid(row=0, column=self.col, pady=5, padx=2, columnspan=1, sticky=tk.NSEW)

class SidebarButtons(Widget):
    def __init__(self, parent, title_text:str=None, columnspan:int=2):
        super().__init__(parent, title_text, columnspan)
        self.col = -1

    def add_button(self, button_text:str, callback=None):
        self.col += 1
        make_button(self.frame, 1, self.col, button_text, callback=callback)

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
        make_button(self.button_frame, 1, self.btn_col, button_text, callback=callback)