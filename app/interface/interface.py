from pathlib import Path

from slicer import Slicer, Gcode, RasterImage
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
        self.window.generate_file += self._genereate_file

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
        '''
        Window close button pressed. Dump config and close application.
        '''
        self.window.dump_config(self.config)
        self.window.close()

    def _trace_file(self, path:Path=None) -> RasterImage:
        '''
        Trace button on sidebar pressed, get or load file, trace it and display on workspace
        '''
        # Get image
        img = self.slicer.get_image(file_path=path, load=True)
        # Trace
        self.window.dump_config(self.config)
        img.trace(self.config)
        # Show
        img.render()
        self.window.show_image(img)

    def _genereate_file(self, path:Path) -> None:
        # Get image
        img = self.slicer.get_image(file_path=path, load=True)
        if not img.traced: self._trace_file(path)
        # Generate
        gcode = Gcode(img)
        gcode.generate(self.config)
        # Show
        self.window.show_gcode(gcode)