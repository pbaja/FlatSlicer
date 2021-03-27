'''
Resolves asset paths
'''
from typing import List
from pathlib import Path

def get_fonts() -> List[Path]:
    fonts = Path('./assets/fonts')
    return list(fonts.glob('*.ttf'))

def get_img(filename) -> Path:
    return Path('./assets/img') / filename