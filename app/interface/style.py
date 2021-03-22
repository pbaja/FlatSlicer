# Window
WINDOW_TITLE = 'Flat Slicer'
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

FONT_LABELS = (FONT_NAME, 9)
FONT_BUTTONS = (FONT_NAME_BOLD, 9)
FONT_TITLES = (FONT_NAME, 11)
FONT_CANVAS = (FONT_NAME_BOLD, 11)
FONT_CANVAS_UI = (FONT_NAME, 8)


# Canvas
CANVAS_BG = '#191b1f'
CANVAS_LINE = '#EEE'
CANVAS_LINE_OUTLINE = '#E84133'
CANVAS_LINE_INFILL = '#cc6c31'
CANVAS_LINE_TRAVEL = '#728ab0'
CANVAS_FILL = '#666'

# Global colors
COLOR_BG0 = '#22252A'
COLOR_BG1 = '#2D3035'
COLOR_BG2 = '#34373D'
COLOR_FG0 = '#DDD'
COLOR_FG1 = '#EEE'


# Ttk style
import tkinter as tk
from tkinter import ttk
class AppStyle(ttk.Style):

    def __init__(self, root):
        super().__init__(root)

    def apply(self):
        self.theme_use('clam')
        self.configure('.', relief='FLAT')

        # Frame
        self.configure('TFrame', background='#22252A', borderwidth=0)

        # Buttons
        self.configure('TButton', background='#2D3035', foreground='#bfc1c4', width=20, borderwidth=0, focusthickness=3, focuscolor='none', font=FONT_BUTTONS)
        self.map('TButton', background=[('active', '#34373d')])

        # Labels
        self.configure('TLabel', background='#22252A', foreground='#bfc1c4', font=FONT_LABELS)
        self.configure('title.TLabel', background='#22252A', anchor=tk.CENTER, foreground='#bfc1c4', font=FONT_TITLES)

        # Entries
        self.configure('TEntry', foreground='#bfc1c4', fieldbackground='#22252A', relief='flat')