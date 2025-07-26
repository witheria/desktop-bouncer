# desktop-bouncer
Make an image bounce on your desktop


This is literally all it does. Read through my lunatic comments if you want to know more.

Setup:

- Clone repository or download file
- create a venv with ```python -m venv .venv``` or smth
- create a folder called ```img``` where you will put the image you want to bounce around
- rename the image to ```we_bounce``` and make sure its either jpg, gif, or png
- install pystray and pillow inside your environment
- run main.py
- close from the system tray icon

Note that there are close to zero safety mechanisms concerning what you _can_ do. If your image is larger than your screen or something, it will _still_ try to bounce it.
Also you can change the framerate freely. Same with upper speed bound and lower speed bound as well as the speed decay on bounce. Its your PC and if you want to try how much it can take I wont be the one to stop you.

Still, be careful :)

Have fun!

(c) Witheria 2024
