#!/bin/bash

# Enter script directory
cd "$(dirname "$0")"

# Create virtual environment
if [ ! -d ".venv" ]
then
    echo "Creating virtual enviroment"
    python3 -m venv .venv || (rm -r .venv ; exit 1)
    source .venv/bin/activate || (rm -r .venv ; exit 2)
    
    echo "Installing requirements"
    pip install -r requirements.txt || (rm -r .venv ; exit 3)
else
    echo "Activating virtual enviroment"
    source .venv/bin/activate || (rm -r .venv ; exit 2)
fi

# Run application
echo "Starting FlatSlicer"
python run.py