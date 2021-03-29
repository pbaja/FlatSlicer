# Run pyinstaller
pyinstaller run.py `
	--onefile `
	--windowed `
	--icon="../assets/img/icon.ico" `
	--name "FlatSlicer" `
	--distpath "./temp/dist" `
	--workpath "./temp/build" `
	--specpath "./temp"

# Copy assets
Copy-Item -Path ".\assets" -Destination ".\temp\dist\assets" -Recurse

# Pause in case of errors
Read-Host -Prompt "Press enter to close"