from enum import IntEnum

class LaserJobTarget(IntEnum):
    Header = 0
    Outline = 1
    Infill = 2
    Footer = 3

class LaserJob:
    def __init__(self, config):
        # Config
        self.min_power = config.get_value('global.min_power')
        self.on_command = config.get_value('global.laser_on')
        self.off_command = config.get_value('global.laser_off')
        self.travel_speed = config.get_value('global.travel_speed')
        self.offset = [config.get_value('global.offset.x'), config.get_value('global.offset.y'), config.get_value('global.offset.z')]
        self.min_travel_sq = config.get_value('global.min_travel_distance') ** 2

        self.outline_power = config.get_value('outline.power')
        self.outline_speed = config.get_value('outline.speed')
        self.infill_power = config.get_value('infill.power')
        self.infill_speed = config.get_value('infill.speed')

        self.infill_passes = config.get_value('infill.passes')
        self.outline_passes = config.get_value('outline.passes')

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

    def __str__(self):
        all_commands = self.cmd_header + (self.cmd_infill * self.infill_passes) + (self.cmd_outline * self.outline_passes) + self.cmd_footer
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
        self.gcode("G90") # Use absolute positioning
        self.gcode("M18 S10") # Disable steppers after 10s of inactivity
        self.gcode("M201 X5000.00 Y5000.00") # Set max acceleration. Default is 500mm/s^2, Prusa uses 9000mm/s^2 for travel
        self.gcode("M204 T5000.00") # Set print acceleration. Default is 500mm/s^2
        self.comment('')
        self.comment('Content')

    def begin_outline(self):
        self.cmd_target = LaserJobTarget.Outline

    def begin_infill(self):
        self.cmd_target = LaserJobTarget.Infill

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
        if len(comment) == 0: self._append('')
        else: self._append(f'; {comment}')

    def gcode(self, command):
        '''Adds raw gcode to the list of commands'''
        self._append(command)

    def move(self, pos, rapid=False):
        '''Moves head to given x,y[,z] coordinates in mm'''
        # Round
        pos = [round(n, 3) for n in pos]
        cmd = "G0 " if rapid else "G1 "
        changed = False
        # X
        if self._pos[0] != pos[0]: 
            cmd += f"X{pos[0] + self.offset[0]} "
            self._pos[0] = pos[0]
            changed = True
        # Y
        if self._pos[1] != pos[1]: 
            cmd += f"Y{pos[1] + self.offset[1]} "
            self._pos[1] = pos[1]
            changed = True
        # Z
        if len(pos) > 2 and self._pos[2] != pos[2]: 
            cmd += f"Z{pos[2] + self.offset[2]} "
            self._pos[2] = pos[2]
            changed = True
        if changed:
            self._append(cmd)

    def speed(self, speed:float):
        '''Changes movement speed. In mm/s'''
        speed = round(float(speed) * 60, 3) # Convert mm/s to mm/min
        if self._speed != speed:
            self._append(f"G1 F{speed}")
            self._speed = speed

    def power(self, power:float, sync=True):
        '''Sets laser power, range from 0.0 to 100.0'''
        power = int(float(power)/100.0*255)
        if self._power != power:
            if sync: self._append("M400")
            self._append(self.on_command.replace("{power}", str(power)))
            self._power = power

    def power_off(self):
        '''Powers off the laser'''
        self._append(self.off_command)
        self.power = None

    def wait(self, ms):
        '''Waits for given ms'''
        self._append(f"G4 P{int(ms)}")
