import json
import math
import sys
import time
import tkinter
from tkinter import messagebox
import PIL.Image
import PIL.ImageTk
import cv2
from pynput import keyboard
from scripts.Message import Message

server_ep = ("127.0.0.1", 50001)
time.sleep(1)


class App:
    def __init__(self, window, window_title, door_to_heaven, server, server_sensors):
        self.window = window
        self.window.title(window_title)
        self.window.configure(background='#cfcfcf')
        self.door_to_heaven = door_to_heaven
        self.server = server
        self.serverSensors = server_sensors
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        self.counter = 0
        self.key_pressed = 'z'
        self.key_released = True

        self.dic_movement_instructions = {
            "move_forward": False,
            "move_backwards": False,
            "rotate_left": False,
            "rotate_right": False
        }

        self.dic_collision = {
            "forward": True,
            "backwards": True,
            "left": True,
            "right": True
        }

        self.dic_sensors = {
            "forward": 100,
            "backwards": 100,
            "left": 100,
            "right": 100
        }

        # LABELS
        self.title_label = tkinter.Label(self.window, text="Robot Controller and Intrusion Detection Interface",
                                         font=("calibri", 30), fg='#cfcfcf',
                                         background='#3d3b3b')
        self.title_label.grid(row=0, column=0, columnspan=2, sticky='nesw')

        self.command_label = tkinter.Label(self.window, text="Press ZQSD to move Robot", font=("calibri", 20),
                                           fg='#3d3b3b',
                                           background='#cfcfcf')
        self.command_label.grid(row=1, column=0)

        self.button_label = tkinter.Label(self.window, text="Control the robot :", font=("calibri", 20),
                                          fg='#3d3b3b',
                                          background='#cfcfcf')
        self.button_label.grid(row=3, column=0, sticky='n')

        # IMAGES

        self.down_green_arrow = PIL.Image.open("../resources/green_arrow.png")
        self.down_white_arrow = PIL.Image.open("../resources/white_arrow.png")
        self.down_green_arrow_img = PIL.ImageTk.PhotoImage(self.down_green_arrow)
        self.down_white_arrow_img = PIL.ImageTk.PhotoImage(self.down_white_arrow)

        self.up_green_arrow = self.down_green_arrow.rotate(180)
        self.up_white_arrow = self.down_white_arrow.rotate(180)
        self.up_green_arrow_img = PIL.ImageTk.PhotoImage(self.up_green_arrow)
        self.up_white_arrow_img = PIL.ImageTk.PhotoImage(self.up_white_arrow)

        self.left_green_arrow = self.down_green_arrow.rotate(-90)
        self.left_white_arrow = self.down_white_arrow.rotate(-90)
        self.left_green_arrow_img = PIL.ImageTk.PhotoImage(self.left_green_arrow)
        self.left_white_arrow_img = PIL.ImageTk.PhotoImage(self.left_white_arrow)

        self.right_green_arrow = self.down_green_arrow.rotate(90)
        self.right_white_arrow = self.down_white_arrow.rotate(90)
        self.right_green_arrow_img = PIL.ImageTk.PhotoImage(self.right_green_arrow)
        self.right_white_arrow_img = PIL.ImageTk.PhotoImage(self.right_white_arrow)

        self.ui_canvas = tkinter.Canvas(window, width=300, height=250, background='#cfcfcf', highlightthickness=0)
        self.ui_canvas.create_image(150, 0, anchor=tkinter.N, image=self.up_white_arrow_img, tags='forward')
        self.ui_canvas.create_image(150, 150, anchor=tkinter.N, image=self.down_white_arrow_img, tags='backwards')
        self.ui_canvas.create_image(75, 75, anchor=tkinter.N, image=self.left_white_arrow_img, tags='left')
        self.ui_canvas.create_image(225, 75, anchor=tkinter.N, image=self.right_white_arrow_img, tags='right')
        self.ui_canvas.grid(row=2, column=0, sticky='nsw')

        self.tracking_canvas = tkinter.Canvas(window, width=960, height=540, highlightthickness=0)
        self.tracking_canvas.grid(column=1, row=2, rowspan=3)

        # BUTTONS

        self.radio_button_var = tkinter.IntVar()
        self.radio_button_var.set(0)
        self.manual_command_rb = tkinter.Radiobutton(self.window, text="manually", variable=self.radio_button_var, value=0,
                                                     command=self.change_mode)
        self.manual_command_rb.grid(row=3, column=0, sticky='s')
        self.auto_command_rb = tkinter.Radiobutton(self.window, text="automatically", variable=self.radio_button_var, value=1)
        self.auto_command_rb.grid(row=4, column=0, sticky='n')

        self.delay = 15
        self.t_prev = time.time()
        self.update_frame()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def update_frame(self):
        self.translate_sensor()

        frame = self.door_to_heaven.get_frame_display_frame()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, (
            math.floor(self.tracking_canvas.winfo_height() * 16 / 9) if self.tracking_canvas.winfo_height() > 100 else math.floor(
                100 * 16 / 9), self.tracking_canvas.winfo_height() if self.tracking_canvas.winfo_height() > 100 else 100))

        self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
        self.tracking_canvas.create_image(0, 0, imag=self.photo, anchor=tkinter.NW)
        self.window.after(self.delay, self.update_frame)

        self.automatic_pid_follower()

    def keydown(self, key):
        if self.radio_button_var.get() == 0:

            for dic_key in self.dic_movement_instructions.keys():
                self.dic_movement_instructions[dic_key] = False

            if key == 'z' and self.dic_collision["forward"]:
                self.dic_movement_instructions["move_forward"] = True
                self.ui_canvas.delete("forward")
                self.ui_canvas.create_image(150, 0, anchor=tkinter.N, image=self.up_green_arrow_img,
                                            tags='forward')
            elif key == 's' and self.dic_collision["backwards"]:
                self.dic_movement_instructions["move_backwards"] = True
                self.ui_canvas.delete("backwards")
                self.ui_canvas.create_image(150, 150, anchor=tkinter.N, image=self.down_green_arrow_img,
                                            tags='backwards')
            elif key == 'q' and self.dic_collision["left"]:
                self.dic_movement_instructions["rotate_left"] = True
                self.ui_canvas.delete("left")
                self.ui_canvas.create_image(75, 75, anchor=tkinter.N, image=self.left_green_arrow_img, tags='left')

            elif key == 'd' and self.dic_collision["right"]:
                self.dic_movement_instructions["rotate_right"] = True
                self.ui_canvas.delete("right")
                self.ui_canvas.create_image(225, 75, anchor=tkinter.N, image=self.right_green_arrow_img,
                                            tags='right')

            self.window.update()
            self.server.send_to(server_ep, Message.command_message(self.dic_movement_instructions["move_forward"],
                                                                   self.dic_movement_instructions["move_backwards"],
                                                                   self.dic_movement_instructions["rotate_left"],
                                                                   self.dic_movement_instructions["rotate_right"]))

    def keyup(self, key):
        if self.radio_button_var.get() == 0:

            if key == 'z':
                self.dic_movement_instructions["move_forward"] = False
                self.ui_canvas.delete("forward")
                self.ui_canvas.create_image(150, 0, anchor=tkinter.N, image=self.up_white_arrow_img,
                                            tags='forward')

            elif key == 's':
                self.dic_movement_instructions["move_backwards"] = False
                self.ui_canvas.delete("backwards")
                self.ui_canvas.create_image(150, 150, anchor=tkinter.N, image=self.down_white_arrow_img,
                                            tags='backwards')

            elif key == 'q':
                self.dic_movement_instructions["rotate_left"] = False
                self.ui_canvas.delete("left")
                self.ui_canvas.create_image(75, 75, anchor=tkinter.N, image=self.left_white_arrow_img, tags='left')

            elif key == 'd':
                self.dic_movement_instructions["rotate_right"] = False
                self.ui_canvas.delete("right")
                self.ui_canvas.create_image(225, 75, anchor=tkinter.N, image=self.right_white_arrow_img,
                                            tags='right')

            self.window.update()
            self.server.send_to(server_ep, Message.command_message(self.dic_movement_instructions["move_forward"],
                                                                   self.dic_movement_instructions["move_backwards"],
                                                                   self.dic_movement_instructions["rotate_left"],
                                                                   self.dic_movement_instructions["rotate_right"]))

    def on_press(self, key):
        try:
            if key.char == 'z' or key.char == 'q' or key.char == 's' or key.char == 'd':
                self.keydown(key.char)
            else:
                pass

        except AttributeError:
            print('special key {0} pressed'.format(
                key))

    def on_release(self, key):
        try:
            if key.char == 'z' or key.char == 'q' or key.char == 's' or key.char == 'd':
                self.keyup(key.char)
            else:
                pass
        except AttributeError:
            print('special key {0} released'.format(
                key))

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.window.destroy()
            sys.exit()

    def translate_sensor(self):
        sensors_message = self.serverSensors.getSensorsMessage()
        self.dic_sensors = json.loads(sensors_message)

        for dic_key in self.dic_sensors.keys():
            if 1.5 > float(self.dic_sensors[dic_key]) > 0.0:
                self.dic_collision[dic_key] = False
            else:
                self.dic_collision[dic_key] = True

        self.robot_navigation()

# robot_navigation allows robot to move depending on some conditions

    def robot_navigation(self):
        if self.radio_button_var.get() == 1:
            for dic_key in self.dic_movement_instructions.keys():
                self.dic_movement_instructions[dic_key] = False

            if self.dic_collision["forward"] and self.counter == 0:
                self.dic_movement_instructions["move_forward"] = True
            else:
                if self.counter == 120:
                    self.counter = 0
                elif self.counter < 120:
                    if self.dic_collision["right"]:
                        self.dic_movement_instructions["rotate_right"] = True
                    elif self.dic_collision["left"]:
                        self.dic_movement_instructions["rotate_left"] = True
                    else:
                        self.dic_movement_instructions["move_backwards"] = True
                        if self.dic_collision["right"]:
                            self.dic_movement_instructions["rotate_right"] = True
                        elif self.dic_collision["left"]:
                            self.dic_movement_instructions["rotate_left"] = True
                    self.counter += 1

            self.server.send_to(server_ep, Message.command_message(self.dic_movement_instructions["move_forward"],
                                                                   self.dic_movement_instructions["move_backwards"],
                                                                   self.dic_movement_instructions["rotate_left"],
                                                                   self.dic_movement_instructions["rotate_right"]))

    def automatic_pid_follower(self):
        b_center = self.door_to_heaven.box_center
        errorx = 960 - b_center[0]
        errorh = 550 - self.door_to_heaven.box_tracked.h
        b_area = self.door_to_heaven.box_tracked.area()

        if b_center != (0, 0) and b_area != 0 and b_area < 400000:
            if errorx > 150:
                self.keydown('q')
                time.sleep(0.01)
                self.keyup('q')
            elif errorx < -150:
                self.keydown('d')
                time.sleep(0.01)
                self.keyup('d')

            if errorh > 90:
                self.keydown('z')
                time.sleep(0.02)
                self.keyup('z')
            elif errorh < -150:
                self.keydown('s')
                time.sleep(0.003)
                self.keyup('s')

    def change_mode(self):
        self.server.send_to(server_ep, Message.command_message())
