import sys, platform
import logging as log
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ctypes import windll, create_string_buffer, byref
from pathlib import Path

from ..utils import Event, assets
from ..slicer import RasterImage, Gcode
from .style import *
from .settings import SettingsWindow 
from .views import WorkspaceView, SidebarView

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
    for font in assets.get_fonts():
        path = str(font)
        if not load_font(path): log.error(f'Failed to load font {font}')
        else: num += 1
    log.info(f'Loaded {num} fonts')


class Window:
    '''
    Creates window and fills it with things
    '''

    def __init__(self) -> None:
        # Private
        self._root:tk.Tk = None
        self._last_selection = 0
        self._sidebar:SidebarView = None
        self._workspace:WorkspaceView = None
        self._settings = None
        # Events
        self.close_pressed = Event()
        self.trace_file = Event()
        self.generate_file = Event()
        self.export_file = Event()
        self.test_octoprint = Event()

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
        self._root.iconbitmap(ICON_FLATSLICER)

        # Apply style
        style = AppStyle(self._root)
        style.apply()

        # Setup window
        window = tk.PanedWindow(self._root)
        window.pack(fill=tk.BOTH, expand=1)

        # Settings window
        self._settings = SettingsWindow(self._root)
        self._settings.octoprint_test_pressed += self.test_octoprint

        # Sidebar
        self._sidebar = SidebarView(window)
        self._sidebar.addfile_pressed += self._addfile_pressed
        self._sidebar.delfile_pressed += self._delfile_pressed
        self._sidebar.trace_pressed += self._trace_pressed
        self._sidebar.generate_pressed += self._generate_pressed
        self._sidebar.export_pressed += self._export_pressed
        self._sidebar.settings_pressed += self._settings_pressed
        self._sidebar.init()
        window.add(self._sidebar.frame)

        # Workspace
        self._workspace = WorkspaceView(window)
        self._workspace.init()
        window.add(self._workspace.frame)

        log.info('Window spawned')

    def _settings_pressed(self):
        self._settings.open()

    def _addfile_pressed(self) -> None:
        filetypes = [('Image files', ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'))]
        filepath = filedialog.askopenfilename(parent=self._root, title='Select file to add', filetypes=filetypes)
        if len(filepath) != 0: 
            listbox = self._sidebar.items['files']
            listbox.insert(tk.END, filepath)

    def _delfile_pressed(self) -> None:
        listbox = self._sidebar.items['files']
        selection = listbox.curselection()
        for x in reversed(selection):
            listbox.delete(x)

    def _get_selected_path(self) -> Path:
        listbox = self._sidebar.items['files']
        selection = listbox.curselection()
        selection = selection[0] if len(selection) > 0 else self._last_selection
        self._last_selection = selection
        path_str = listbox.get(selection)
        if not len(path_str):
            messagebox.showwarning('No file selected', 'No files has been selected. Select file first.')
            return None
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
        if len(gcode_path) > 0:
            gcode_path = Path(gcode_path)
            self.export_file(path, gcode_path)
        else:
            log.warn('Exporting cancelled, no output path specified')

    def show_image(self, image:RasterImage):
        '''
        Changes or refreshes currently displayed image
        '''
        self._workspace.show_img(image)

    def show_gcode(self, gcode:Gcode):
        '''
        Changes or refreshes currently displayed gcode. Hides polygon lines.
        '''
        self._workspace.show_gcode(gcode)

    def load_config(self, cfg):
        '''
        Loads config values to sidebar
        '''
        self._sidebar.load_config(cfg)
        self._settings.load_config(cfg)

    def dump_config(self, cfg):
        '''
        Dumps values from sidebar items to config
        '''
        self._sidebar.dump_config(cfg)
        self._settings.dump_config(cfg)

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
