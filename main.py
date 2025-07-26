#!/usr/bin/env python3

# (i dont know what that thing above does, i found it on stackoverflow and they said its important)

# (C) Toni Schmidbauer / Witheria 2024

# fun and stupid image on desktop bouncer (?) for your lolz
# Use with caution, do not distribute without changing my dumb comments
# If someone somehow makes a virus out of this im sorry and not legally liable

# TO USE:
# - put this python file somewhere safe
# - create venv, install pillow and pisstray (its called pystray [the voices]), activate venv
# - create a folder in that safe spot called "img"
# - put in whatever image you want to bounce on your desktop (png, gif, jpg) 
# - Call that image "we_bounce" (leave file extension like it was before)
# - python main.py
# - IT BOUNCES MY GUY
# - close it with the tray icon once you had enough

# If you have multiple files called "we_bounce" with valid file extensions it selects one arbitrarily

# You can throw the image by double clicking it and dragging it.
# Make sure to drag and release it properly or windows fucks with you and it _WILL_ give you epilepsy
# (it wont)
# (im not legally liable for any misuse, medical emergencies and/or thermonuclear wars this causes)
# (im not legally liable for anything this script does)
# (in fact i overdosed on caffeine, pretty sure i couldnt even be legally liable if i wanted to)
# (THIS PROGRAM IS PROVIDED "AS IS", NO LICENSE, NO RESPONSIBILITY. YOU USE IT, YOU ARE RESPONSIBLE)

# I might have an exe as a zip floating around but im not gonna be the one taking responsibility for 
# your "windows defender has blocked malicious software" popup (your grandma asking if the program is safe)
# (i sold her data to the CCP) [for legal reasons I didnt] {yet}

# HAVE FUN!


import tkinter as tk
import random
import os
import ctypes

from PIL import Image

import pystray


# i made this at 3 am 
# if you dont like it think of that
# my nightmares dont care about your coding conventions
TRAY_ICON: pystray.Icon = None
IMG_FOLDER = "img"
ALLOWED_IMG_TYPES = ["png", "jpg", "gif"]
CWD_PATH = os.path.abspath(".")


def random_with_extra_steps(start: int, stop: int, lower_bound: int) -> int:
    # function to exclude a range with randrange (0 speed is boring af)
    # also, i know there are more efficient methods to do this, but i didnt want to think
    # range is symmetric (lower and upper bound also applies to negative numbers)
    if stop < lower_bound:
        # ts just loops infinitely otherwise which is not too good.
        return lower_bound
    
    while True:
        v = random.randrange(start, stop, 1)
        if lower_bound < abs(v):
            return v


def getImage() -> str:
    # function to get a "we_bounce" named item in the img folder
    # allows for simple swapping :))
    # the file always needs to be called "we_bounce", file ext needs to be in allowed_img_types
    file_name = "we_bounce"

    if not os.path.exists("img"):
        raise FileNotFoundError("You better create that img directory somewhere I can find it!")
    
    with os.scandir("img") as scan:
        for entry in scan:
            if entry.is_file():
                if entry.name.startswith(file_name) and entry.name.split(".")[-1] in ALLOWED_IMG_TYPES:
                    return entry.name
    # ^ this looks horrible but idk works well enough ig
    raise FileNotFoundError("You better make sure to create and rename the file!")


def getIMGData(imgpath) -> dict:
    # This method tries to get the number of image frames (if applicable) and size
    im = Image.open(imgpath)
    if imgpath.endswith("gif"):
        return {
            "frames": getattr(im, "n_frames", 1),
            "size": im.size,
            "gif": True
        }
    return {
        "size": im.size,
        "gif": False
    }


class Bouncer(tk.Toplevel):

    # i recommend anything between 5 (slideshow) and 60 (pro gamer)
    # if you go above that, you will notice the window going MUCH faster once you hover over it
    # i believe this is because windows prioritizes the process you "act" in and gives it more resources
    # you wont be able to catch the window anymore once you go over a certain threshhold :))
    framerate: int = 60

    # image stuff
    _img_path: str  # path to image (xd hope you didnt guess something else)
    _img_data: list  # images as a list (if not a gif contains only the main image)
    _img_size: list  # width height
    _gif_speed: float = 80  # time per gif frame in ms (gets rounded to framerate)
    _gif_length: int = 1  # how many frames does the gif have. static images have 1
    _gif_cycle: int = 0  # position in the gif (which image is displayed). if not a gif remains unchanged
    _gif_frame_cycle: int = 0  # counts frames until gif_cycle should change

    # Movement stuff
    _speed: list = [0, 0]  # velocity x, velocity y of the window
    _base_speed: list = []  # saves the starting speed (gets rolled)
    _position: list = []  # x position, y position of the window
    _movement_speed: int = 1  # how many gif cycles it should count before doing a movement step
    # ^ this is a remnant from when i made movement == gif framerate and didnt have a separate framerate
    _movement_cycle: int = 0  # dont know how to document this mess, just try and understand it idk
                              # with this one you can offset the movement steps to the framerate
                              # If movement speed = 2, movement happens only every second frame
    _upper_base_speed_per_second: int = 150  # amount in pixels the image should travel at most per second
    _lower_base_speed_per_second: int = 15  # amount in pixels the image should travel at least per second

    _screen_data: tuple = ()  # width, height of the virtual screen (as per windows funny api)
    # If the image has speed above base speed this will be multiplied with it until its back to low
    _speed_decay: float = 0.85  # on each bounce. i forgot to mention, it only reduces speed on bounce

    # stuff for tray
    is_bouncer_hidden = False  # is the window currently hidden or not
    _movable = False  # is the window currently movable by mouse drag or not

    # If you drag it, it might go weeee, so we save wee
    _drag_speed_data: list[list[int]] = [[0, 0], [0, 0]]  # amount of data, avg of data

    # This one is here so it only does the 4 checks on speed if it know it can be fast
    # waste of resources and i dont think this is an optimization but i dont care enough
    _has_drag_speed: list[bool] = [False, False]

    # If we have a gif, we need to animate it properly and do funny stuff (end me)
    _is_gif_image: bool = False
    
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.parent = parent  # dont need it but eh
        self.overrideredirect(True)  # disable windows header bar
        self.config(highlightbackground=self['bg'])  # this makes background standard color
        self.label = tk.Label(self, bd=0, bg=self['bg'])  # this makes label background also standard
        # self.wm_attributes('-transparentcolor', 'black')
        self.wm_attributes('-transparentcolor', self['bg'])  # this makes standard color transparent
        self.attributes('-topmost',True)  # ALWAYS ON TOP HAHA (dont choose giga large image)
        self.label.pack()

        # i dont like this but i also dont care enough
        self.dragx = 0
        self.dragy = 0

        # overwrite gif speed with stupid calculation because i love fps but hate maths
        # this sets a relative count of frames instead of the ms value (so you can change the fps
        # but the frametime stays roughly the same)
        self._gif_speed = self._gif_speed // (1000 // self.framerate)

        self.withdraw()  # Withdraw until setup is finished

        # bind all the mouse stuff to the label
        self.label.bind("<ButtonPress-1>", self.start_move)  # mouseclick starts drag
        self.label.bind("<ButtonRelease-1>", self.stop_move)  # mouserelease stops drag
        self.label.bind("<B1-Motion>", self.do_move)  # mouse move while clicking drags window
        self.label.bind('<Double-Button-1>', self.change_movable)  # double click changes moveability (?xd)

    def setIMG(self, img_path):
        # only do all this if the image path is valid and exists
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"File not found: {img_path}")
        
        self._img_path = img_path  # set image path of the class
         
        data = getIMGData(self._img_path)  # get information about the image
        
        self._is_gif_image = data["gif"]  # is the image a gif or not
        self._img_size = data["size"]  # how big is it

        if self._is_gif_image:
            # special treatment for animation 
            # get gif length
            self._gif_length = data["frames"]
            
            # split that gif into its images
            self._img_data = [
                    tk.PhotoImage(file=self._img_path, 
                                format = 'gif -index %i' %(i)) 
                            for i in range(self._gif_length)]
            
        else:
            self._gif_length = 0
            self._img_data = [tk.PhotoImage(file=self._img_path)]

        # show it on the label before we even start the cycle
        self.label.configure(image=self._img_data[self._gif_cycle])

    def initScreen(self, screen_data):
        self._screen_data = screen_data

        # apply padding so window doesnt spawn/move outside of screen
        self._screen_data = [self._screen_data[x] - self._img_size[x] for x in range(2)]

        # roll the window position
        self._position = [random.randrange(0, self._screen_data[0]), 
                          random.randrange(0, self._screen_data[1])]
        self.geometry(f"{self._img_size[0]}x{self._img_size[1]}+{self._position[0]}+{self._position[1]}")

        # roll window speed (two fancy random numbers)
        self.generateSpeed()

        self._base_speed = self._speed

        print("Random position is: ", self._position)
        print("Random speed is (x,y):", self._speed)
        print("Random base speed is (x,y):", self._base_speed)

        # now actually spawn the window itself
        self.deiconify()

        # into the loop it goes
        self.after(1000 // self.framerate, self.update)

    def generateSpeed(self):
        # had to make this its own method simply because of how it looks
        self._speed = [
            random_with_extra_steps(
                start=-self._upper_base_speed_per_second,
                stop=self._upper_base_speed_per_second,
                lower_bound=self._lower_base_speed_per_second
            ) / self.framerate,
            random_with_extra_steps(
                start=-self._upper_base_speed_per_second,
                stop=self._upper_base_speed_per_second,
                lower_bound=self._lower_base_speed_per_second
            ) / self.framerate
        ]
        return self._speed

    def update(self):
        # +1 frame cycle
        self._movement_cycle += 1
        bounce = False  # <-- this one saves whether the image bounced this call or not

        if self._movement_cycle == self._movement_speed:
            # this below moves the image to the new position
            self._position[0] -= self._speed[0]
            self._position[1] -= self._speed[1]
            self.geometry(
                f"{self._img_size[0]}x{self._img_size[1]}+{int(self._position[0])}+{int(self._position[1])}"
                )
            self._movement_cycle = 0

        # There needs to be an if statement for every case because we could be overshooting the wall/floors
        # and then wed be stuck in a permanent loop, so to combat that i will reset the position when it hits 
        # but for this i need to know in which direction it tried to go
        # its always the following: 
        #   invert speed value (so it goes other direction)
        #   set position to 1 pixel inbounds (so we dont loop randomly)
        #   set bounce to true so we knew we bounced over here 
        if self._position[0] >= self._screen_data[0]:
            self._speed[0] *= -1
            self._position[0] = self._screen_data[0] - 1
            bounce = True
            print("Bounced at right monitor wall, new speed: ", self._speed)
        
        elif self._position[0] <= 0:
            self._speed[0] *= -1
            self._position[0] = 1
            bounce = True
            print("Bounced at left monitor wall, new speed: ", self._speed)

        if self._position[1] >= self._screen_data[1]:
            self._speed[1] *= -1
            self._position[1] = self._screen_data[1] - 1 
            bounce = True
            print("Bounced at monitor bottom, new speed: ", self._speed)
        
        elif self._position[1] <= 0:
            self._speed[1] *= -1
            self._position[1] = 1
            bounce = True
            print("Bounced at monitor top, new speed: ", self._speed)

        if bounce and any(self._has_drag_speed):
            # now this is to decay the drag speed
            # the gif might have LOTS of speed and it should decay once it bounces
            # again, one for x coordinates and one for y coordinates

            if abs(self._speed[0]) > abs(self._base_speed[0]):
                # decay the speed if its too fast
                self._speed[0] *= self._speed_decay
            elif abs(self._speed[0]) < abs(self._base_speed[0]):
                # if the speed is below base speed, just set it to base speed and set flag to false
                self._speed[0] = self._base_speed[0]
                self._has_drag_speed[0] = False

            if abs(self._speed[1]) > abs(self._base_speed[1]):
                self._speed[1] *= self._speed_decay
            elif abs(self._speed[1]) < abs(self._base_speed[1]):
                self._speed[1] = self._base_speed[1]
                self._has_drag_speed[1] = False
        
        if self._is_gif_image:  # Only reconfigure image if we actually need to (if its a gif)
            self._gif_frame_cycle += 1
            if self._gif_frame_cycle == self._gif_speed:
                # remember: gif speed is the amount of frames (counted in gif_frame_cycle) that need to pass 
                # until we swap gif image. 
                self._gif_cycle += 1
                self._gif_frame_cycle = 0

                if self._gif_cycle == self._gif_length:
                    self._gif_cycle = 0
                
                # reconfigure new gif image on the label
                self.label.configure(image=self._img_data[self._gif_cycle])

        # loop (call same function again)
        self.after(1000 // self.framerate, self.update)

    def change_movable(self, event):
        # Catches double click event to change throwability (?is this english?)
        self._movable = not self._movable
        print(f"Bouncer is now movable: {self._movable}")

    def start_move(self, event):
        if self._movable:
            self.dragx = event.x
            self.dragy = event.y
        print("start move", self._base_speed, self._speed)

    def stop_move(self, event):
        print("stop move", self._base_speed, self._speed)
        if self._movable:
            try:
                self.dragx = 0
                self.dragy = 0

                # we dont allow 0 as speed value so i always 10 * random it
                if self._drag_speed_data[0][1] == 0:
                    self._drag_speed_data[0][1] = random.random()
                if self._drag_speed_data[1][1] == 0:
                    self._drag_speed_data[1][1] = random.random()

                # for some reason this goes in the wrong direction xd?
                # Also i multiply by two for better feel 
                self._speed[0] = self._drag_speed_data[0][1] * -2
                self._speed[1] = self._drag_speed_data[1][1] * -2
                self._has_drag_speed = [True, True]
            except Exception as e:
                print(e)
            print("Drag finished! New Speed: ", self._speed)

            # Reset the drag speed data list for next drag
            self._drag_speed_data = [[0, 0], [0, 0]]

    def do_move(self, event):
        # @TODO (bug: mouse gets treated as a wall and speed conversion is weird)
        if self._movable:
            self._speed = [0, 0]
            deltax = event.x - self.dragx
            deltay = event.y - self.dragy
            self._position[0] = self.winfo_x() + deltax
            self._position[1] = self.winfo_y() + deltay

            # This looks horrible but i just get the dynamic averages of the drag movement
            # Also i cut off speed that is under 10 because i dont want SLOW LOL
            if abs(deltax) > 10:
                # only last 5 frames get averaged to ensure direction
                if self._drag_speed_data[0][0] > 5:  
                    self._drag_speed_data[0] = [0, 0]

                # add one to the amount of data then (N*avg + new)/(N + 1)
                self._drag_speed_data[0][0] += 1 
                self._drag_speed_data[0][1] = \
                    (self._drag_speed_data[0][0]*self._drag_speed_data[0][1] + deltax) / \
                    (self._drag_speed_data[0][0] + 1)

            if abs(deltay) > 10:
                if self._drag_speed_data[1][0] > 5:
                    self._drag_speed_data[1] = [0, 0]

                self._drag_speed_data[1][0] += 1 
                self._drag_speed_data[1][1] = \
                    (self._drag_speed_data[1][0]*self._drag_speed_data[1][1] + deltay) / \
                    (self._drag_speed_data[1][0] + 1)

            # set new geometry
            self.geometry(f"+{self._position[0]}+{self._position[1]}")

    def quit_window(self):
        # close window. Still needs the tray icon, so it can be closed too (global crimnge)        
        if not TRAY_ICON:
            return
        
        # this does what it says so i wont comment it. Look at the documentation for questions i cba
        TRAY_ICON.visible = False
        TRAY_ICON.stop()
        self.parent.quit()

    def show_cat(self):
        # show the window
        self.is_bouncer_hidden = False
        self.after(0, self.deiconify)
        print("Showed bouncer", not self.is_bouncer_hidden)

    def hide_cat(self):
        # hide the window
        self.is_bouncer_hidden = True
        self.withdraw()
        print("Hid bouncer", self.is_bouncer_hidden)
    
    def get_bouncer_hidden(self, menu_item: pystray._base.MenuItem):
        # returns if the bouncer is currently hidden according to the menu item text
        if menu_item.text == "Show":
            return self.is_bouncer_hidden
        return not self.is_bouncer_hidden


class App(tk.Tk):

    bouncer: Bouncer

    def __init__(self, imgpath):
        tk.Tk.__init__(self)

        # DONT EVEN LET THIS ABOMINATION SHOW FOR A SECOND
        self.withdraw()

        # create subwindow class
        self.bouncer = Bouncer(self)
        self.bouncer.setIMG(imgpath)

        # OLD METHOD WITH TKINTER (only gets active monitor resolution)
        # getting monitor res with this would be only possible here
        self.bouncer.initScreen([self.winfo_screenwidth(), self.winfo_screenheight()])

        # NEW METHOD WITH WINDOWS API (gets entire virtual monitor resolution)
        # This makes the thing work with multiple monitors, even though there could be weird side effects
        # i do it here anyway because it centralizes setup idk the voices told me so
        # Just uncomment if you want to use it. Works bad with different resolutions
        # user32 = ctypes.windll.user32
        # self.bouncer.initScreen([user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)])


def setup_tray(tray_window, tray_icon_path):
    # horrible method but the package is cool. i like pisstray
    global TRAY_ICON

    tray_menu_not_hidden = (
        # menu items for the tray menu. one of "hide" and "show" is always hidden depending on state
        pystray.MenuItem("Hide", tray_window.hide_cat, visible=tray_window.get_bouncer_hidden),
        pystray.MenuItem("Show", tray_window.show_cat, visible=tray_window.get_bouncer_hidden),
        # "make it bubble up", make it bubble up yourself work loving refactor guy in my head
        pystray.MenuItem('Quit', tray_window.quit_window) 
    )
    tray_image = Image.open(tray_icon_path)

    # actually initialize the tray icon now
    TRAY_ICON = pystray.Icon("DA BOUNCE", tray_image, "We bouncin'", tray_menu_not_hidden)
    
    # make it run in its own thread
    TRAY_ICON.run_detached()


if __name__ == "__main__":
    
    # yeeees this is proper image path indeed
    this_is_proper_image_path = os.path.join(CWD_PATH, IMG_FOLDER, getImage())

    # definitely did not test if this random ass function works or not
    # print(15 in [random_with_extra_steps(-100, 100, 15) for _ in range(1000)]

    app = App(imgpath=this_is_proper_image_path)
    setup_tray(app.bouncer, this_is_proper_image_path)
    app.mainloop()
