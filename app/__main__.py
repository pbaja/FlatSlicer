import logging as log
import sys

if __name__ == '__main__':

    # Python version check
    major, minor, *_ = sys.version_info
    if major < 3 or minor < 6:
        print(f'Python {major}.{minor} is not supported. At least Python 3.6 is required')
        sys.exit(1)

    # Python architecture check
    if sys.maxsize <= 2**32//2:
        print(f'For best results Python 64bit is required.')
        if 'ignore_x64' in sys.argv[1:]:
            sys.exit(1)

    # Configure logging module
    log.basicConfig(level=log.INFO, format='[%(levelname)s] %(message)s')
    log.info(f'Starting')

    # Load configuration
    from utils import Config
    config = Config()
    config.load()

    # Create slicer instance
    from slicer import Slicer
    slicer = Slicer()

    # Create interface instance
    from interface import Interface
    interface = Interface()

    # Initialize and start
    slicer.init()
    interface.init(slicer, config)
    interface.load_config()
    interface.main()

    # Quit
    config.save()

'''
    # Debug
    import sys
    from pathlib import Path
    from slicer import Slicer
    slicer = Slicer()
    img = slicer.load_image(Path(sys.argv[0]).parent.parent / 'blobs.png')
    img.convert()
    img.show()


'''