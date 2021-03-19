import json, sys
import logging as log
from pathlib import Path

class Config:

    default_data = {
        'files': [
            # No files loaded by default
        ],
        'import': {
            'dpi': 508,
            'epsilon': 0.5
        },
        'global': {
            'laser_on': 'M106 P1 S{power}',
            'laser_off': 'M107 P1',
            'min_power': 1.0,
            'offset': {'x': 0, 'y': 0, 'z': 20.0},
            'travel_speed': 100.0,
            'bezier_resolution': 0.1,
            'min_travel_distance': 0.12
        },
        'outline': {
            'passes': 1,
            'power': 100.0,
            'speed': 20.0
        },
        'infill': {
            'passes': 0,
            'power': 70.0,
            'speed': 15.0,
            'line_spacing': 0.1
        }
    }

    def __init__(self, filepath='config.json'):
        self.path = Path(sys.path[0]).parent / filepath
        self.data = {}

    def get_value(self, path:str, source=None):
        keys = path.split('.')
        item = self.data if source is None else source
        for i, key in enumerate(keys):
            # Is this last key
            last = i == len(keys)-1
            # Get item
            if last: key = keys[-1].rsplit(':', 1)[0]
            if key in item:
                item = item[key]
                if last: return item
            else: 
                # Item not found, try searching in default data
                if source is None:
                    log.warn(f'Entry "{path}" not found in config, searching in default data')
                    default = self.get_value(path, Config.default_data)
                    if default is not None:
                        self.set_value(path, default)
                        return default
                # Not found in default data either
                return None
        return None

    def set_value(self, path:str, value):
        # Find dictionary at path
        keys = path.split('.')
        item = self.data
        for key in keys[:-1]:
            if not key in item:
                item[key] = {}
            item = item[key]

        # Set value with parsing
        key = keys[-1].rsplit(':', 1)
        key_name = key[0]
        try:
            if len(key) > 1 and isinstance(value, str):
                key_type = key[1]
                if key_type == 'int': value = int(value)
                elif key_type == 'float': value = float(value)
        except Exception as e:
            print(f'exception: {e}')
            print(f'key_name: {key_name}')
            print(f'key_type: {key_type}')
            print(f'value: {value}')
        item[key_name] = value

    def save(self):
        with self.path.open('w+') as f:
            json.dump(self.data, f, indent=4)
            log.info('Saved config to file')

    def load(self):
        if not self.path.is_file():
            self.data = Config.default_data
            log.info('Loaded default config')
            self.save()
        else:
            with self.path.open('r') as f:
                self.data = json.load(f)
                log.info('Loaded config from file')