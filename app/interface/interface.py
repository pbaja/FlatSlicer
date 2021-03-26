import logging as log
from pathlib import Path
from tkinter import messagebox

from slicer import Slicer, Gcode, RasterImage
from utils import Event, Config, Octoprint, OctoprintResult
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
        self.window.export_file += self._export_file
        self.window.test_octoprint += self._test_octoprint

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

    def _trace_file(self, path:Path=None) -> None:
        '''
        Trace button on sidebar pressed, get or load file, trace it and display on workspace
        '''
        # Get image
        img = self.slicer.get_image(file_path=path, load=True)
        if img is None: return
        self.window.dump_config(self.config)
        # Check dpi
        if img.exif_dpi is not None:
            if self.config.get_value('image.dpi') != img.exif_dpi:
                msg = f'Loaded file contains information about DPI that is different from entered value.\n\nDo you want to update entered value to {img.exif_dpi}?' 
                if messagebox.askyesno('Different DPI', msg):
                    self.config.set_value('image.dpi', img.exif_dpi)
                    self.window.load_config(self.config)
        # Trace
        img.trace(self.config)
        # Show
        img.render()
        self.window.show_image(img)

    def _genereate_file(self, path:Path) -> None:
        # Get image
        img = self.slicer.get_image(file_path=path, load=True)
        if img is None: return
        if not img.traced: self._trace_file(path)
        # Generate
        self.window.dump_config(self.config)
        gcode = Gcode(img)
        gcode.generate(self.config)
        img.gcode = gcode
        # Show
        self.window.show_gcode(gcode)
        
    def _export_file(self, path:Path, gcode_path:Path) -> None:
        # Get image
        img = self.slicer.get_image(file_path=path, load=True)
        if img is None: return
        if not img.traced: self._trace_file(path)

        # Make sure image gcode has been generated
        if img.gcode is None:
            messagebox.showwarning('No Gcode found', 'Generate Gcode first by pressing "Generate Gcode".')
            log.warn('Tried to save gcode, but no gcode has been generated')
            return

        # Generate output
        output = img.gcode.get_output()
        if output is None:
            log.error('Failed to generate Gcode')
            return

        # Save to file
        with gcode_path.open('w+') as f:
            f.write(output)
            log.info(f'Saved Gcode to {path}')

        # Upload to octoprint
        if self.config.get_value('octoprint.enabled'):
            Octoprint.upload(self.config, gcode_path.name, output)

    def _test_octoprint(self):
        self.window.dump_config(self.config)
        result, version = Octoprint.server_version(self.config)
        if result == OctoprintResult.Success:
            messagebox.showinfo('Success', f'Connected successfully.\nOctoPrint version: {version}')
            self.config.set_value('octoprint.enabled', True)
        else:
            messagebox.showwarning('Failed', f'Failed to connect to OctoPrint.\nReason: {result.name}\n\n{version}')
            self.config.set_value('octoprint.enabled', False)