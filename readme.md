# Rust Fleet Watchlist

##Client Dependecies
* numpy
* PIL
* cv2
* win32gui

## Packaging the Executable
Install [py2exe](http://www.py2exe.org). Then run the following command:

`cd client && python setup.py py2exe`

If it complains about missing `numpy-atlas.dll`, copy `%SITE_PACKAGES%\numpy\core\numps-atlas.dll` to the client directory.
