from pathlib import Path

from slicer import Slicer, RasterImage
from utils import Event, Config
from .window import Window


class Interface:
    '''
    Creates and manages window, passes events
    '''

    def __init__(self):
        '''
        Define fields
        '''
        self.window = Window()
        self.config:Config = None
        self.slicer:Slicer = None

    def init(self, slicer:Slicer, config:Config) -> None:
        '''
        Create and initialize window. Hook events.
        '''
        self.config = config
        self.slicer = slicer

        self.window.init()
        self.window.close_pressed += self._close_pressed
        self.window.trace_file += self._trace_file

    def load_config(self) -> None:
        '''
        Display values from config on UI
        '''
        self.window.load_config(self.config)

    def main(self) -> None:
        '''
        Starts main loop (blocking)
        '''
        try:
            self.window.run()
        except KeyboardInterrupt:
            self._close_pressed()

    def _close_pressed(self):
        self.window.dump_config(self.config)
        self.window.close()

    def _trace_file(self, path:Path):
        img = self.slicer.get_image(file_path=path)
        if img is None: img = self.slicer.load_image(file_path=path)

        img.trace()
        img.render()
        
        self.window.show_image(img)
