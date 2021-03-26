import json, sys
import logging as log
from typing import Dict, List
from pathlib import Path

default_data = {

    # Settings
    'octoprint': {
        'enabled': False,
        'url': '',
        'key': ''
    },
    'machine': {
        'laser_on': 'M106 P1 S{power}',
        'laser_off': 'M107 P1',
        'min_power': 1.0,
        'travel_speed': 100.0,
        'min_travel': 0.5,
        'travel_accel': 2000.0,
        'burn_accel': 5000.0,
    },

    # Config
    'files': [],
    'image': {
        'dpi': 508,
        'offset': {'x': 0, 'y': 0, 'z': 20.0}
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

class Config:

    def __init__(self):
        self.base_path:Path = Path(sys.path[0]).parent
        self.default_data = self._flatten(default_data)
        self.data:Dict = {}

    def _flatten(self, target, path=''):
        '''
        Flattens data from nested to a dot-separated keys
        '''
        result = {}
        for key, value in target.items():
            new_path = path + f'.{key}' if len(path) else key
            if isinstance(value, dict): 
                result.update(self._flatten(value, new_path))
            else:
                result[new_path] = value
        return result

    def _inflate(self, target, path=''):
        '''
        Inflates data from dot-separated keys to nested
        '''
        result = {}
        for key, value in target.items():
            self._inflate_key(key, value, result)
        return result

    def _inflate_key(self, key, value, output):
        key, *rest = key.split('.', 1)
        if rest: self._inflate_key(rest[0], value, output.setdefault(key, {}))
        else: output[key] = value

    def get_value(self, path:str, source=None):
        # Ignore type modifier
        key = path.rsplit(':', 1)[0]

        # Get from data
        if source is None: 
            if key not in self.data:
                # Not found, try defaults
                return self.get_value(path, self.default_data)
            return self.data[key]
        # Get from source
        else:
            return source.get(key, None)

    def set_value(self, path:str, value):
        try:
            # Get path and type
            key = path.rsplit(':', 1)
            key_path = key[0]
            key_type = 'str' if len(key) < 2 else key[1]

            # Parse type
            if key_type == 'int': value = int(value)
            elif key_type == 'float': value = float(value)

            # Set value
            self.data[key_path] = value
        except ValueError:
            log.error(f'Failed to set value. Could not convert "{key_path}" value: "{value}"" to {key_type}')

    def _write(self, target:Dict, file_path:Path, keys:List):
        with file_path.open('w+') as f:
            result = {k: target[k] for k in target.keys() and set(keys)}
            json.dump(result, f, indent=4)

    def _read(self, target:Dict, file_path:Path):
        if not file_path.is_file(): 
            return None
        with file_path.open('r') as f:
            target.update(self._flatten(json.load(f)))

    def save(self):
        inflated = self._inflate(self.data)
        self._write(inflated, self.base_path / 'settings.json', ['machine', 'octoprint'])
        self._write(inflated, self.base_path / 'config.json', ['files', 'import', 'outline', 'infill'])
        log.info('Saved config to files')

    def load(self):
        self.data = {}
        self._read(self.data, self.base_path / 'settings.json')
        self._read(self.data, self.base_path / 'config.json')
        log.info('Loaded config from files')