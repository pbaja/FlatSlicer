import math, gc, random
import logging as log
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk


from utils import PerfTool
from slicer import RasterImage, Gcode
from .view import View
from .style import *

class WorkspaceView(View):

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas:tk.Canvas = None
        self._scale = 1.0
        self._anchor_id = None
        self._raster_img = None # Raster image
        self._img = None # Original image
        self._img_scaled = None # Scaled image
        self._img_cropped = None # Cropped image
        self._img_id = None
        self._tkimg = None
        self._line_ids = []
        self._motion_pos = None
        self._gcode_calctime = None

    def init(self):
        '''
        Create canvas
        '''
        self.canvas = tk.Canvas(self.frame, bg=CANVAS_BG)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<MouseWheel>', self._wheel)  # windows and mac
        self.canvas.bind('<Button-5>',   self._wheel)  # linux, scroll down
        self.canvas.bind('<Button-4>',   self._wheel)  # linux, scroll up
        self.canvas.bind('<ButtonPress-1>', lambda event: self.canvas.scan_mark(event.x, event.y))
        self.canvas.bind('<ButtonRelease-1>', self._motion_end)
        self.canvas.bind("<B1-Motion>", self._motion)

        self._anchor_id = self.canvas.create_text(0, 0, anchor='nw', text='', fill='gray', font=FONT_CANVAS)

        _ = (0,0,0,0)
        self._ui_ids = [
            self.canvas.create_line(_, width=1, fill='white'),
            self.canvas.create_line(_, width=1, fill='white'),
            self.canvas.create_line(_, width=1, fill='white'),
            self.canvas.create_text(0, 0, anchor='n', text='', fill='gray', font=FONT_CANVAS_UI),
            self.canvas.create_text(0, 0, anchor='ne', text='', fill='gray', font=FONT_CANVAS_UI)
        ]
        self._update_ui()

    def _update_ui(self):
        if self._raster_img:
            # Calculate scale width
            width = self._raster_img.info_mm2pix * self._scale
            if width > 275: mm = 1
            elif width > 24: mm = 2
            elif width > 5: mm = 10
            else: mm = 50
            width *= mm

            # Scale lines
            x0 = self.canvas.canvasx(10)
            x1 = x0 + width
            y = self.canvas.canvasy(self.canvas.winfo_height()-10)
            self.canvas.coords(self._ui_ids[0], x0, y-5, x0, y+5)
            self.canvas.coords(self._ui_ids[1], x0, y, x1, y)
            self.canvas.coords(self._ui_ids[2], x1, y-5, x1, y+5)

            # Scale text
            self.canvas.itemconfig(self._ui_ids[3], text=f'{mm}mm')
            self.canvas.coords(self._ui_ids[3], x0+(width/2), y-17)
            
            # Info text
            size = self._img.size
            mpix = round(size[0] * size[1] / 10**6, 1)
            mm2pix = self._raster_img.info_mm2pix
            size = size[0]/mm2pix, size[1]/mm2pix
            img = self._raster_img
            info = f'{size[0]}mm x {size[1]}mm, {img.info_numlines} lines, {img.info_numpolygons} polygons, {mpix} Mpix in {img.info_calctime} ms'
            if self._gcode_calctime is not None:
                info += f', gcode: {self._gcode_calctime} ms'
            self.canvas.itemconfig(self._ui_ids[4], text=info)
            x = self.canvas.canvasx(self.canvas.winfo_width()-10)
            self.canvas.coords(self._ui_ids[4], x, y-10)

            # Lift all
            for e in self._ui_ids: self.canvas.lift(e)

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
        if self._scale > 15.0: self._scale = 15.0
        if self._scale < 0.1: self._scale = 0.1
        scale = self._scale / prev_scale
        # Rescale all canvas objects
        mouse_x, mouse_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.scale('all', mouse_x, mouse_y, scale, scale)
        for line_id in self._line_ids:
            width = int(line_id[1] * self._scale)
            self.canvas.itemconfig(line_id[0], width=max(width, 1))
        # Scale image
        if self._tkimg is not None:
            self._scale_image()
            self._crop_image()
            self._update_image()
        # Update text
        self.canvas.itemconfig(self._anchor_id, text=f'x{round(self._scale,1)}')
        self._update_ui()

    def _motion(self, event):
        # Drag canvas
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self._update_ui()
        # Update image every 50 pixels
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
        pos = self.canvas.coords(self._anchor_id)
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
        # Convert PIL image to TK image
        self._tkimg = ImageTk.PhotoImage(image=self._img_cropped)
        if self._img_id:
            # Reuse canvas image object
            self.canvas.itemconfig(self._img_id, image=self._tkimg)
            self.canvas.coords(self._img_id, self._img_pos[0], self._img_pos[1])
        else:
            # Create new canvas image object
            self._img_id = self.canvas.create_image(self._img_pos, anchor='nw', image=self._tkimg, tag='img')
            self.canvas.lower(self._img_id)

    def _clear_lines(self):
        for line_id in self._line_ids: self.canvas.delete(line_id[0])
        self._line_ids.clear()

    def show_img(self, image:RasterImage):
        '''
        Display image on canvas
        '''
        # Save dpi
        self._img = image.image
        self._raster_img = image
        self._update_ui()

        # Remove previous lines
        self._clear_lines()

        # Display raster image
        self._scale_image()
        self._crop_image()
        self._update_image()

        # Display polygons
        colors = ['#EE4D4D', '#FF884D', '#FFC44D', '#8BC94D', '#4DDBC4', '#4DC4FF', '#5E94FF', '#A071FF', '#FF4DA5']
        offset = self.canvas.coords(self._anchor_id)
        for i, polygon in enumerate(image.polygons):
            # Flatten array of points
            flat_points = []
            for x, y in polygon:
                flat_points.append((x + 0.5)*self._scale + offset[0])
                flat_points.append((y + 0.5)*self._scale + offset[1])
            # Add line
            line_id = self.canvas.create_line(*flat_points, fill=colors[i%len(colors)], width=int(self._scale))
            self._line_ids.append((line_id, int(self._scale)))

    def _draw_gcode(self, commands, line_color, travel_color, width=1.0):
        prev_cmd = None
        px, py = 0, 0
        offset = self.canvas.coords(self._anchor_id)
        points = [px * self._scale + offset[0], py * self._scale + offset[1]]

        single_color = False
        if len(commands) > 40_000:
            log.warn(f'Too many lines. Travel moves will be displayed with same color as burn lines.')
            single_color = True

        for gstr in commands:
            # Parse
            params = gstr.split()
            if len(params) == 0: continue
            cmd = params[0]

            # Move command
            if cmd == 'G0' or cmd == 'G1':
                # Target x, y
                tx, ty = px, py
                for param in params[1:]:
                    if param[0] == 'X': tx = float(param[1:]) + 0.5
                    elif param[0] == 'Y': ty = float(param[1:]) + 0.5
                # Draw polygon if skipped first and cmd changed
                if not single_color and prev_cmd is not None and cmd != prev_cmd:
                    self._add_polyline(points, prev_cmd, line_color, travel_color, width)
                    points.clear()
                    points += [px * self._scale + offset[0], py * self._scale + offset[1]]
                # Add current point
                points += [tx * self._scale + offset[0], ty * self._scale + offset[1]]
                prev_cmd = cmd
                px, py = tx, ty
        if len(points) >= 4:
            self._add_polyline(points, prev_cmd, line_color, travel_color, width)

    def _add_polyline(self, points, cmd, line_color, travel_color, width):
        # Properties
        fill = line_color if cmd == 'G1' else travel_color
        if cmd == 'G0': width *= 0.5
        # Arrow
        arrow = tk.NONE
        if len(points) == 4:
            length = np.sqrt((points[2]-points[0])**2 + (points[3]-points[1])**2)
            if length * self._scale / self._raster_img.info_mm2pix > 2.0: # Add arrows for >2.0mm * scale
                arrow = tk.LAST
        # Add line
        line_id = self.canvas.create_line(*points, fill=fill, arrow=arrow, width=int(width*self._scale))
        self._line_ids.append((line_id, width))

    def show_gcode(self, gcode:Gcode):
        # Remove previous lines
        self._clear_lines() 
        # Draw outline lines
        self._draw_gcode(gcode.job.cmd_outline, CANVAS_LINE_OUTLINE, CANVAS_LINE_OUTLINE_TRAVEL)
        # Draw infill lines
        self._draw_gcode(gcode.job.cmd_infill, CANVAS_LINE_INFILL, CANVAS_LINE_INFILL_TRAVEL, width=0.01)
        # Save calctime
        self._gcode_calctime = gcode.info_calctime
        self._update_ui()