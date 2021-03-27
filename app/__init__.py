'''
Top level application module containing two main submodules: interface, slicer and utils
'''
import logging as log
import sys

from .version import VERSION_STR


def run():
    # Python version check
    major, minor, *_ = sys.version_info
    if major < 3 or minor < 6:
        print(f'Python {major}.{minor} is not supported. At least Python 3.6 is required')
        sys.exit(1)

    # Python architecture check
    if sys.maxsize <= 2**32//2:
        print(f'For best results Python 64bit is required.')
        if 'ignore_x64' not in sys.argv[1:]:
            sys.exit(1)

    # Configure logging module
    log.getLogger('numba.core.ssa').setLevel(log.WARN)
    log.getLogger('numba.core.interpreter').setLevel(log.WARN)
    log.getLogger('numba.core.byteflow').setLevel(log.WARN)
    log.getLogger('numba.core.typeinfer').setLevel(log.WARN)
    log.getLogger('PIL.PngImagePlugin').setLevel(log.WARN)
    log.getLogger('PIL.Image').setLevel(log.WARN)
    log.getLogger('urllib3.connectionpool').setLevel(log.WARN)
    log.basicConfig(level=log.DEBUG, format='[%(levelname)s] %(message)s')
    log.info(f'Starting FlatSlicer v{VERSION_STR}')

    # Load configuration
    from .utils import Config
    config = Config()
    config.load()

    # Create slicer instance
    from .slicer import Slicer
    slicer = Slicer()

    # Create interface instance
    from .interface import Interface
    interface = Interface()

    # Initialize and start
    slicer.init()
    interface.init(slicer, config)
    interface.load_config()
    interface.main()

    # Quit
    config.save()