# Yet another image viewer for linux
While trying different image viewers for KDE Plasma I realised that all these dozens of apps have 2 things in common: 
1. they are either provide just image viewer without any small additional tools like cropping or rotating
2. or they do have all these and much more tools but their weight is somewhat unacceptable.


That's why I decided to create my own ideal viewer providing only features that I need and nothing more 
while keeping the already small laptop memory for more usefull programs.

# What's inside?
For this task I wanted to use `python` and it's libraries.
Interface is built with flutter (python `flet` library) because it's modern (not like `tkinter`) and easy to use (not like `pyqt`).
For images processing I use `pillow` and `pathlib` for managing paths.


And that's it!