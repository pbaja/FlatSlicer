import sys
import tkinter as tk
from tkinter import ttk
from ..utils import assets

# Window

from .. import VERSION_STR
WINDOW_TITLE = f'Flat Slicer v{VERSION_STR}'
WINDOW_SIZE = (1280, 720)

# Fonts

import platform
system = platform.system()
if system == 'Windows':
    FONT_NAME = 'Montserrat'
    FONT_NAME_BOLD = 'Montserrat SemiBold'
elif system == 'Linux':
    FONT_NAME = 'Ubuntu'
    FONT_NAME_BOLD = 'Ubuntu Medium'
else:
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica Bold'

FONT_SMALL = (FONT_NAME, 8)
FONT_LABELS = (FONT_NAME, 10)
FONT_BUTTONS = (FONT_NAME_BOLD, 9)
FONT_BUTTONS_SMALL = (FONT_NAME_BOLD, 8)
FONT_TITLES = (FONT_NAME_BOLD, 11)
FONT_HEADERS = (FONT_NAME_BOLD, 12)
FONT_CANVAS = (FONT_NAME_BOLD, 11)
FONT_CANVAS_UI = (FONT_NAME, 8)

# Icons
ICON_FLATSLICER = str(assets.get_img('icon.ico'))
ICON_SETTINGS = str(assets.get_img('settings.png'))

# Canvas

CANVAS_BG = '#191b1f'
CANVAS_LINE = '#EEE'
CANVAS_LINE_INFILL = '#45B0E5'
CANVAS_LINE_INFILL_TRAVEL = '#7D8995'
CANVAS_LINE_OUTLINE = '#D64545'
CANVAS_LINE_OUTLINE_TRAVEL = '#8B98A6'
CANVAS_FILL = '#666'

# Global colors

COLOR_FG0 = '#FFF'
COLOR_FG1 = '#bfc1c4'
COLOR_FG2 = '#AFAFAF'

COLOR_BG0 = '#22252A'
COLOR_BG1 = '#2D3035'
COLOR_BG2 = '#34373D'

# TTK style

class AppStyle(ttk.Style):

    def __init__(self, root):
        super().__init__(root)

    def apply(self):
        self.theme_use('default')
        self.configure('.', relief='FLAT')

        # Frame
        self.configure('TFrame', background=COLOR_BG0, borderwidth=0)
        self.configure('header.TFrame', background='#23272D', borderwidth=0)

        # Buttons
        self.configure('TButton', background=COLOR_BG1, foreground=COLOR_FG1, width=20, borderwidth=0, focusthickness=3, focuscolor='none', font=FONT_BUTTONS)
        self.map('TButton', background=[('active', COLOR_BG2)])
        self.configure('header.TButton', font=FONT_BUTTONS_SMALL)

        # Labels
        self.configure('TLabel', background=COLOR_BG0, foreground=COLOR_FG1, font=FONT_LABELS)
        self.configure('title.TLabel', background=COLOR_BG0, anchor=tk.CENTER, foreground=COLOR_FG1, font=FONT_TITLES)
        self.configure('header.TLabel', background='#23272D', anchor=tk.CENTER, foreground='#65AED9', font=FONT_HEADERS)
        self.configure('desc.TLabel', background='#23272D', anchor=tk.CENTER, foreground=COLOR_FG2, font=FONT_SMALL)

        # Entries
        self.configure('TEntry', foreground=COLOR_FG1, fieldbackground=COLOR_BG0, relief='flat')

        # Notebook
        self.configure("TNotebook", background=COLOR_BG0, borderwidth=0)
        self.configure("TNotebook.Tab", foreground=COLOR_FG0, borderwidth=0)
        self.map("TNotebook.Tab", background=[("selected", COLOR_BG2), ("!selected", COLOR_BG1)])