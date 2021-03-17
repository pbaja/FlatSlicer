import sys, platform
import logging as log
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ctypes import windll, create_string_buffer, byref
from pathlib import Path

from utils import Event
from .style import *
from .sidebar import SidebarView
from .workspace import WorkspaceView

def _load_fonts() -> None:
    # Unfortuanely currently we support loading custom fonts only on windows
    if platform.system() != 'Windows':
        log.warn(f'Using default font. Loading custom fonts is available only on windows.')
        return

    # Custom method
    def load_font(path:str) -> bool:
        # Prepare args and handle
        path_buf = create_string_buffer(path.encode())
        flags_int = 0x10 | 0x20 # Private | Enumerable
        AddFontResource = windll.gdi32.AddFontResourceExA
        
        # Execute
        numFontsAdded = AddFontResource(byref(path_buf), flags_int, 0)
        return bool(numFontsAdded)

    # Load all fonts from /fonts directory
    num = 0
    fonts = Path(sys.path[0]).parent / 'fonts'
    for font in fonts.glob('*.ttf'):
        path = str(font)
        if not load_font(path):
            log.error(f'Failed to load font {font}')
        else:
            num += 1
    log.info(f'Loaded {num} fonts')


class Window:
    '''
    Creates window and fills it with things
    '''

    def __init__(self) -> None:
        # Private
        self._root:tk.Tk = None
        # Public
        self.sidebar:SidebarView = None
        self.workspace:WorkspaceView = None
        # Events
        self.close_pressed = Event()
        self.trace_file = Event()
        self.generate_file = Event()
        self.export_file = Event()

    def init(self):
        '''
        Prepares gui environment and spawns window
        '''
        # Init fonts
        _load_fonts()
        # Setup root
        self._root = tk.Tk()
        self._root.tk_setPalette(background=COLOR_BG0, foreground=COLOR_FG0, activeBackground=COLOR_BG0, activeForeground=COLOR_FG0)
        self._root.title(WINDOW_TITLE)
        self._root.minsize(*WINDOW_SIZE)
        self._root.protocol("WM_DELETE_WINDOW", self.close_pressed)
        # Apply style
        style = AppStyle(self._root)
        style.apply()
        # Setup window
        window = tk.PanedWindow(self._root)
        window.pack(fill=tk.BOTH, expand=1)

        # Sidebar
        self.sidebar = SidebarView(window)
        self.sidebar.addfile_pressed += self._addfile_pressed
        self.sidebar.delfile_pressed += self._delfile_pressed
        self.sidebar.trace_pressed += self._trace_pressed
        self.sidebar.generate_pressed += self._generate_pressed
        self.sidebar.export_pressed += self._export_pressed
        self.sidebar.init()
        window.add(self.sidebar.frame)

        # Workspace
        self.workspace = WorkspaceView(window)
        self.workspace.init()
        window.add(self.workspace.frame)

        log.info('Window spawned')

    def _addfile_pressed(self) -> None:
        filetypes = [('Image files', ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'))]
        filepath = filedialog.askopenfilename(parent=self._root, title='Select file to add', filetypes=filetypes)
        if len(filepath) != 0: 
            listbox = self.sidebar.items['files']
            listbox.insert(tk.END, filepath)

    def _delfile_pressed(self) -> None:
        listbox = self.sidebar.items['files']
        selection = listbox.curselection()
        for x in reversed(selection):
            listbox.delete(x)

    def _get_selected_path(self) -> Path:
        listbox = self.sidebar.items['files']
        selection = listbox.curselection()
        selection = selection[0] if len(selection) > 0 else 0
        path_str = listbox.get(selection)
        return Path(path_str)

    def _trace_pressed(self) -> None:
        path = self._get_selected_path()
        self.trace_file(path)

    def _generate_pressed(self) -> None:
        path = self._get_selected_path()
        self.generate_file(path)

    def _export_pressed(self) -> None:
        path = self._get_selected_path()
        filename = path.name.rsplit('.', 1)[0] + '.gcode'
        filetypes = [('Gcode', '*.gcode')]
        gcode_path = filedialog.asksaveasfilename(parent=self._root, title='Select filename', initialfile=filename, filetypes=filetypes)
        self.export_file(path, gcode_path)

    def load_config(self, cfg):
        '''
        Loads config values to sidebar
        '''
        for path, item in self.sidebar.items.items():
            value = cfg.get_value(path)
            # Fill items
            if isinstance(item, tk.Entry):
                item.delete(0, tk.END)
                item.insert(0, str(value))
            elif isinstance(item, tk.Listbox):
                for x in value:
                    item.insert(tk.END, x)

    def dump_config(self, cfg):
        '''
        Dumps values from sidebar items to config
        '''
        for path, item in self.sidebar.items.items():
            if isinstance(item, tk.Entry):
                cfg.set_value(path, item.get())
            elif isinstance(item, tk.Listbox):
                cfg.set_value(path, list(item.get(0, item.size())))

    def run(self):
        '''
        Runs tkinter main loop
        '''
        self._root.mainloop()

    def close(self) -> None:
        '''
        Stops tkinter main loop
        '''
        self._root.quit()
