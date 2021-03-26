import app

if __name__ == '__main__':
    app.run()


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