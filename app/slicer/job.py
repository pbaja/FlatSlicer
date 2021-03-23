from enum import IntEnum

class LaserJobTarget(IntEnum):
    Header = 0
    Outline = 1
    Infill = 2
    Footer = 3

class LaserUnit(IntEnum):
    Pixels = 0
    Milimeters = 1

class LaserCmd:
    def valid(self):
        return True

class LaserMove(LaserCmd):
    def __init__(self, x, y, z, unit:LaserUnit, rapid:bool):
        self.x = x
        self.y = y
        self.z = z
        self.rapid = rapid
        self.unit = unit
        self.applied = False
    def valid(self):
        return (self.x is not None) or (self.y is not None) or (self.z is not None)
    def __str__(self):
        if not self.valid(): return ''
        args = []
        if self.x is not None: args.append(f"X{round(self.x,3)}")
        if self.y is not None: args.append(f"Y{round(self.y,3)}")
        if self.z is not None: args.append(f"Z{round(self.z,3)}")
        args.insert(0, 'G0' if self.rapid else 'G1')
        return ' '.join(args)

class LaserRaw(LaserCmd):
    def __init__(self, code):
        self.code = code
    def __str__(self):
        return self.code

class LaserJob:
    def __init__(self, config):
        # Config
        self.min_power = config.get_value('machine.min_power')
        self.on_command = config.get_value('machine.laser_on')
        self.off_command = config.get_value('machine.laser_off')
        self.travel_speed = config.get_value('machine.travel_speed')
        self.offset = [config.get_value('machine.offset.x'), config.get_value('machine.offset.y'), config.get_value('machine.offset.z')]

        self.outline_power = config.get_value('outline.power')
        self.outline_speed = config.get_value('outline.speed')
        self.outline_passes = config.get_value('outline.passes')
        self.infill_power = config.get_value('infill.power')
        self.infill_speed = config.get_value('infill.speed')
        self.infill_passes = config.get_value('infill.passes')

        # Commands
        self.cmd_target = None
        self.cmd_header = []
        self.cmd_outline = []
        self.cmd_infill = []
        self.cmd_footer = []

        # Current state
        self._power = 0
        self._speed = 0
        self._pos = [-1, -1, -1]

    def _apply(self, commands, height_mm, pix2mm):
        for cmd in commands:
            # Only move commands
            if not isinstance(cmd, LaserMove): continue
            # Skip already processed
            # if cmd.applied: continue
            # cmd.applied = True
            # Convert pixels to mm
            if cmd.unit == LaserUnit.Pixels:
                if cmd.x is not None: cmd.x *= pix2mm
                if cmd.y is not None: cmd.y *= pix2mm
                if cmd.z is not None: cmd.z *= pix2mm
                cmd.unit = LaserUnit.Milimeters
                # Flip y
                if cmd.y is not None: cmd.y = height_mm - cmd.y
            # Add offset
            if cmd.x is not None: cmd.x += self.offset[0]
            if cmd.y is not None: cmd.y += self.offset[1]
            if cmd.z is not None: cmd.z += self.offset[2]

    def apply(self, height, pix2mm):
        '''
        Goes over all commands, flips Y coordinate and converts pixels to mm
        This is done here, at the end, because all other libs have 0,0 in top left corner.
        '''
        self._apply(self.cmd_header, height, pix2mm)
        self._apply(self.cmd_outline, height, pix2mm)
        self._apply(self.cmd_infill, height, pix2mm)
        self._apply(self.cmd_footer, height, pix2mm)

    def __str__(self):
        all_commands = self.cmd_header + (self.cmd_infill * self.infill_passes) + (self.cmd_outline * self.outline_passes) + self.cmd_footer
        all_commands = [str(cmd) for cmd in all_commands if cmd.valid()]
        return "\n".join(all_commands)

    def begin_header(self):
        self.cmd_target = LaserJobTarget.Header
        self.comment('')
        self.comment('Generated with Flatslicer')
        self.comment(' https://github.com/pbaja/Flatslicer')
        self.comment('')
        self.comment('Header')
        self.power(self.min_power)
        self.speed(self.travel_speed)
        self.gcode("G21") # Use metric system
        self.gcode("G90") # Use absolute positioning (G21->relative)
        self.gcode("M18 S10") # Disable steppers after 10s of inactivity
        self.gcode("M201 X5000.00 Y5000.00") # Set max acceleration. Default is 5000mm/s^2, Prusa uses 9000mm/s^2 for travel
        self.gcode("M204 T5000.00") # Set print acceleration. Default is 5000mm/s^2

    def begin_outline(self):
        self.cmd_target = LaserJobTarget.Outline
        self.comment('')
        self.comment('Outline pass')

    def begin_infill(self):
        self.cmd_target = LaserJobTarget.Infill
        self.comment('')
        self.comment('Infill pass')

    def end(self):
        self.cmd_target = LaserJobTarget.Footer
        self.comment('')
        self.comment('Footer')
        self.power_off()
        self.speed(self.travel_speed)
        self.move([0, 0, 0], True)

    # Operations

    def travel(self, target):
        '''
        Turns off laser, changes speed to travelling speed, moves to target
        '''
        self.power(self.min_power)
        self.speed(self.travel_speed)
        self.move(target, rapid=True)

    def burn(self, target):
        '''
        Changes speed to burn speed, turns on laser, moves to target
        '''
        speed = None
        if self.cmd_target == LaserJobTarget.Outline:  speed = self.outline_speed
        elif self.cmd_target == LaserJobTarget.Infill: speed = self.infill_speed
        else: raise Exception(f'Unknown burn speed for {self.cmd_target}')

        power = None
        if self.cmd_target == LaserJobTarget.Outline:  power = self.outline_power
        elif self.cmd_target == LaserJobTarget.Infill: power = self.infill_power
        else: raise Exception(f'Unknown power for {self.cmd_target}')

        self.speed(speed)
        self.power(power)
        self.move(target)

    # Low level functions

    def _append(self, line):
        if self.cmd_target == LaserJobTarget.Header:
            self.cmd_header.append(line)
        elif self.cmd_target == LaserJobTarget.Outline:
            self.cmd_outline.append(line)
        elif self.cmd_target == LaserJobTarget.Infill:
            self.cmd_infill.append(line)  
        elif self.cmd_target == LaserJobTarget.Footer:
            self.cmd_footer.append(line)

    def comment(self, comment):
        '''Adds comment'''
        if len(comment) == 0: self._append(LaserRaw(''))
        else: self._append(LaserRaw(f'; {comment}'))

    def gcode(self, command):
        '''Adds raw gcode to the list of commands'''
        self._append(LaserRaw(command))

    def move(self, pos, unit=LaserUnit.Pixels, rapid=False, force=False):
        '''Moves head to given x,y[,z] coordinates in mm'''

        x, y, z = None, None, None
        if abs(self._pos[0]-pos[0]) > 0.001: 
            x = pos[0]
            self._pos[0] = pos[0]
        if abs(self._pos[1]-pos[1]) > 0.001: 
            y = pos[1]
            self._pos[1] = pos[1]
        if len(pos) > 2 and abs(self._pos[2]-pos[2]) > 0.001: 
            z = pos[2]
            self._pos[2] = pos[2]

        m = LaserMove(x, y, z, unit=unit, rapid=rapid)
        if m is not None: self._append(m)

    def speed(self, speed:float):
        '''Changes movement speed. In mm/s'''
        if abs(self._speed-speed) > 0.001:
            speed_mm_min = round(float(speed) * 60, 3)  # Convert mm/s to mm/min
            self._append(LaserRaw(f"G1 F{speed_mm_min}"))
            self._speed = speed

    def power(self, power:float, sync=True):
        '''Sets laser power, range from 0.0 to 100.0'''
        if abs(self._power-power) > 0.001:
            power_256 = int(float(power)/100.0*255)
            if sync: self._append(LaserRaw("M400"))
            self._append(LaserRaw(self.on_command.replace("{power}", str(power_256))))
            self._power = power

    def power_off(self):
        '''Powers off the laser'''
        if self._power != 0:
            self._append(LaserRaw(self.off_command))
            self._power = 0

    def wait(self, ms):
        '''Waits for given ms'''
        self._append(LaserRaw(f"G4 P{int(ms)}"))
