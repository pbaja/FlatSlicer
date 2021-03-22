<p align="center">
<img align="center" src="img/glowtie.png" alt="Screenshot">
</p>

## Description  
FlatSlicer is a tool that generates Gcode from raster images (png, jpeg, etc.) for lasers. It will extract and trace polygons from image and then generate outline/infill in optimized way.  
  
Useful for making PCBs, engraving text, shapes, cool patterns.  
Not suitable for engraving images (does not support grayscale).  
  
## Usage  
Eventually I want to provide installer with binaries that will be available to download at the Releases page.  
For now you can run it directly from the source:  
 - Make sure that [python](https://www.python.org/downloads/) is installed
 - Download source code from [https://github.com/pbaja/FlatSlicer/archive/refs/heads/main.zip](here)
 - Unzip it
 - **Windows:** Right click on `run.ps1` and select `Run with PowerShell`
 - **Linux:** Execute `run.sh` from the terminal
 - On the first run the script will automatically create venv and install all dependencies
  
## Documentation  
The project is at a very early stage, the GUI and functionality is constantly changing. Documentation will appear on the Wiki page after the project will be more or less in beta not in alpha state.  