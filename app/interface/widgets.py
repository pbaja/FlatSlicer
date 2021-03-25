import tkinter as tk
from .style import *

def make_frame(parent):
    frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.pack(expand=True, fill=tk.BOTH)
    return frame

def make_label(parent, row, col, text, col_weight=1, col_span=1, pad_y=2, pad_x=5, style='TLabel', anchor=tk.W, desc=None):
    # If there is description, create subframe
    if desc is not None:
        parent = tk.Frame(parent)
        parent.grid(row=row, column=col, padx=pad_x, pady=pad_y, columnspan=col_span, sticky=tk.NSEW)
        row = 0
        col = 0
        pad_y = 0
        pad_x = 0
        col_span = 1
        col_weight = 1
    # Create label
    label = ttk.Label(parent, text=text, style=style, anchor=anchor)
    label.columnconfigure(col, weight=col_weight)
    label.grid(row=row, column=col, padx=pad_x, pady=pad_y, columnspan=col_span, sticky=tk.NSEW)
    # Create description
    if desc is not None:
        label = ttk.Label(parent, text=desc, anchor=anchor, style='desc.'+style)
        label.columnconfigure(col, weight=col_weight)
        label.grid(row=1, column=0, padx=pad_x, columnspan=col_span, sticky=tk.NSEW)

def make_entry(parent, row, col, validate=None, col_weight=1, width=25):
    # Create entry
    entry = tk.Entry(parent, width=width, validate='all')
    entry.configure(relief='flat', background=COLOR_BG1)
    # Configure layout
    entry.columnconfigure(col, weight=col_weight)
    entry.grid(row=row, column=col, padx=5, pady=2, sticky=tk.E)
    # Handle input
    entry.insert(0, '-')
    if validate is not None: entry.config(validatecommand=(parent.register(validate), '%P'))
    return entry

def make_button(parent, row, col, label, col_span=1, width=5, sticky=tk.NSEW, callback=None):
    # Create button
    none_func = lambda: None
    btn = ttk.Button(parent, text=label, width=width, command=none_func if callback is None else callback)
    # Configure layout
    parent.columnconfigure(col, weight=1)
    btn.grid(row=row, column=col, pady=5, padx=2, columnspan=col_span, sticky=sticky)
    return btn

def validate_int(value:str) -> bool:
    try:
        if len(value) != 0: int(value) # Parseable to int
        return len(value) <= 1 or value[0] != '0' or value[0] != ' ' or value[-1] != ' '
    except:
        return False

def validate_float(value:str) -> bool:
    try:
        if len(value) != 0: float(value) # Parseable to float
        return len(value) <= 1 or value[0] != '0' or value[0] != ' ' or value[-1] != ' '
    except:
        return False

def title_row(parent, row, title, col_span=2):
    '''
    Large title text
    '''
    make_label(parent, row, 0, title, style='title.TLabel', pad_y=5, col_span=col_span)

def entry_row(parent, row, label, validate=None, desc=None):
    '''
    Label and entry combo. Optional description.
    '''
    make_label(parent, row, 0, label, desc=desc, pad_x=(15, 5))
    return make_entry(parent, row, 1, validate=validate)