import math
import tkinter as tk

from .view import View
from .style import *

class WorkspaceView(View):

    def __init__(self, parent):
        super().__init__(parent)

    def init(self):
        self.canvas = tk.Canvas(self.frame, bg=CANVAS_BG)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def clear(self):
        self.canvas.delete('all')

    def display_lines(self, drawing, scale):
        # Help method for drawing points
        def draw(points, filled):
            flat_points = []
            for point in points:
                point *= scale
                flat_points.append(point.x)
                flat_points.append(point.y)
            if filled:
                self.canvas.create_polygon(*flat_points, fill=CANVAS_FILL, outline=CANVAS_LINE)
            else:
                self.canvas.create_line(*flat_points, fill=CANVAS_LINE)

        # Iterate over all polygons
        for polygon in drawing.polygons:

            # Convert lines to points
            first = polygon.lines[0]
            points = [first.start]
            for idx, line in enumerate(polygon.lines):
                prev = points[-1]
                dist = (prev - line.start).len() #  math.sqrt(pow(prev.x-line.start.x, 2) + pow(prev.y-line.start.y, 2))
                if dist > 0.01 and len(points) > 2: 
                    draw(points, polygon.filled)
                    points.clear()
                    points.append(line.start)
                    points.append(line.end)
                    points.append(polygon.lines[idx+1].start)
                else:
                    points.append(line.end)
            if len(points) > 2: 
                draw(points, polygon.filled)

    def display_gcode(self, drawing, scale):
        self.draw_gcode(drawing.job.cmd_outline, scale, CANVAS_LINE_OUTLINE)
        self.draw_gcode(drawing.job.cmd_infill, scale, CANVAS_LINE_INFILL)

    def draw_gcode(self, commands, scale, color):
        # Previous x, y
        px, py = 0, 0
        for line in commands:
            params = line.split()
            if len(params) > 0:
                cmd = params[0]
                # Move command
                if cmd == 'G0' or cmd == 'G1':
                    # Target x, y
                    tx, ty = px, py
                    for param in params[1:]:
                        if param[0] == 'X': tx = float(param[1:])
                        elif param[0] == 'Y': ty = float(param[1:])
                    # Draw line
                    fill = color if cmd == 'G1' else CANVAS_LINE_TRAVEL
                    points = [px, py, tx, ty]
                    points = [p*scale for p in points]
                    self.canvas.create_line(*points, fill=fill)
                    px = tx
                    py = ty

    def display(self, drawing):
        if drawing.job is None:
            self.display_lines(drawing, 10)
        else:
            self.display_gcode(drawing, 10)
            print('drawing has gcode')