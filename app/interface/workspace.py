import math, gc, random
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk

from slicer import RasterImage
from .view import View
from .style import *

class WorkspaceView(View):

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas:tk.Canvas = None
        self._scale = 1.0
        self._text_id = None
        self._img = None # Original image
        self._img_scaled = None # Scaled image
        self._img_cropped = None # Cropped image
        self._img_id = None
        self._tkimg = None
        self._line_ids = []
        self._motion_pos = None

    def init(self):
        '''
        Create canvas
        '''
        self.canvas = tk.Canvas(self.frame, bg=CANVAS_BG)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<MouseWheel>', self._wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self._wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self._wheel)
        self.canvas.bind('<ButtonPress-1>', lambda event: self.canvas.scan_mark(event.x, event.y))
        self.canvas.bind('<ButtonRelease-1>', self._motion_end)
        self.canvas.bind("<B1-Motion>", self._motion)

        self._text_id = self.canvas.create_text(0, 0, anchor='nw', text='Scroll to zoom')

    def _wheel(self, event):
        '''
        Zoom with mouse wheel
        '''
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        scale = 1.0
        prev_scale = self._scale
        if event.num == 5 or event.delta == -120: self._scale /= 1.25
        if event.num == 4 or event.delta == 120: self._scale *= 1.25
        # Clamp scale
        if self._scale > 10.0: self._scale = 10.0
        if self._scale < 0.1: self._scale = 0.1
        scale = self._scale / prev_scale
        # Rescale all canvas objects
        mouse_x, mouse_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.scale('all', mouse_x, mouse_y, scale, scale)
        for line_id in self._line_ids:
            self.canvas.itemconfig(line_id, width=int(self._scale))
        # Scale image
        if self._tkimg is not None:
            self._scale_image()
            self._crop_image()
            self._update_image()
        # Constrain view box
       # self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.canvas.itemconfig(self._text_id, text=f'x{round(self._scale,1)}')

    def _motion(self, event):
        # Drag canvas
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        # Update image every few pixels
        pos = (event.x, event.y)
        if self._motion_pos is None: self._motion_pos = pos
        dist = abs(pos[0] - self._motion_pos[0])**2 + abs(pos[1] - self._motion_pos[1])**2
        if dist > 50**2:
            self._motion_pos = pos
            self._motion_end(event)

    def _motion_end(self, event):
        # Update image
        if self._tkimg is not None:
            self._crop_image()
            self._update_image()

    def _scale_image(self):
        # Calculate new size
        new_size = int(self._scale * self._img.size[0]), int(self._scale * self._img.size[1])
        # Scale image
        self._img_scaled = self._img.resize(new_size, Image.NEAREST)

    def _crop_image(self):
        # View box in canvas space
        pos = self.canvas.coords(self._text_id)
        pos = [int(pos[0]), int(pos[1])]
        view_box = (
            self.canvas.canvasx(0) - pos[0],
            self.canvas.canvasy(0) - pos[1],
            self.canvas.canvasx(self.canvas.winfo_width()) - pos[0],
            self.canvas.canvasy(self.canvas.winfo_height()) - pos[1],
        )

        # Image box visible in view box
        new_size = self._img_scaled.size
        padding = 50
        crop = (
            min(new_size[0], max(view_box[0] - padding, 0)), # Left
            min(new_size[1], max(view_box[1] - padding, 0)), # Upper
            new_size[0] - min(new_size[0], max(new_size[0]-view_box[2]-padding, 0)), # Right
            new_size[1] - min(new_size[1], max(new_size[1]-view_box[3]-padding, 0)), # Bottom
        )

        # Save image position
        self._img_pos = (
            crop[0] + pos[0],
            crop[1] + pos[1],
        )

        # Crop image
        self._img_cropped = self._img_scaled.crop(box=crop)

    def _update_image(self):
        # Remove previous
        if self._img_id:
            self.canvas.delete(self._img_id)
            self._tkimg = None
            gc.collect()

        # Add new
        self._tkimg = ImageTk.PhotoImage(image=self._img_cropped)
        self.canvas.delete('img')
        self._img_id = self.canvas.create_image(self._img_pos, anchor='nw', image=self._tkimg, tag='img')
        self.canvas.lower(self._img_id)

    def show(self, image:RasterImage):
        '''
        Display image on canvas
        '''

        # Remove previous lines
        for line_id in self._line_ids: self.canvas.delete(line_id)
        self._line_ids.clear()

        # Display raster image
        self._img = image.image
        self._scale_image()
        self._crop_image()
        self._update_image()

        # Display polygons
        colors = ["#%06x"%random.randint(0,16777215) for _ in range(10)]
        offset = self.canvas.coords(self._text_id)
        for polygon in image.polygons:
            # Flatten array of points
            flat_points = []
            for x, y in polygon:
                flat_points.append((x + 0.5)*self._scale + offset[0])
                flat_points.append((y + 0.5)*self._scale + offset[1])
            # Add line
            line_id = self.canvas.create_line(*flat_points, fill=random.choice(colors), width=int(self._scale))
            self._line_ids.append(line_id)