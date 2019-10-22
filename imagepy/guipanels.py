'''

Module to manage button and image panels of the main GUI window

Created by Gabriele Nasello on Oct 16 2018

'''

import tkinter as tk
from tkinter import ttk

class ButtonPanel(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        #self.grid_rowconfigure(1, weight=20)
        btn_frame = ButtonsFrame(self, controller)

        btn_frame.grid(row=0, column=0, sticky="nsew")


class ImagePanel(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        color = '#%02x%02x%02x' % (220, 218, 213)  # background color of ttk widgets in Hex color format
        self.configure(background = color)
        self.grid_columnconfigure(0, weight=10)
        self.grid_rowconfigure(0, weight=10)
        self.grid_rowconfigure(1, weight=1)


class ButtonsFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        color = '#%02x%02x%02x' % (220, 218, 213)  # background color of ttk widgets in Hex color format
        self.configure(background = color)

        norows = 8
        for row in range(norows):
            self.grid_rowconfigure(row, weight=1)

        self.grid_columnconfigure(0, weight=1)
        #self.grid_columnconfigure(1, weight=1)

        # controller.procesbtn = ttk.Button(self, text="Process ROI", command = lambda: controller.img.processed.apply_threshold())
        # controller.procesbtn.config(state="disabled")
        #
        # controller.modifybtn = ttk.Button(self, text="Modify Processing", command = lambda: controller.img.processed.open_modify())
        # controller.modifybtn.config(state="disabled")

        controller.manual_imbtn = ttk.Button(self, text="Manual Selector", command = lambda: controller.img.processed.manual_selector())
        controller.manual_imbtn.config(state="disabled")

        controller.lbl_cell_list = ttk.Label(self, text='Cell Processed List', font=("Arial", 10))
        controller.lbl_cell_list.configure(anchor="center")
        controller.lbl_cell_list.config(state="disabled")

        controller.cell_list = tk.StringVar() # value = countrynames
        controller.lbox = tk.Listbox(self, listvariable = controller.cell_list)
        controller.lbox.config(state="disabled")

        controller.display_selectedbtn = ttk.Button(self, text="Display Selected Cell", command = lambda: controller.img.processed.display_cell_selected())
        controller.display_selectedbtn.config(state="disabled")

        controller.modifyBodyBtn = ttk.Button(self, text="Mod Body Skel", command = lambda: controller.img.processed.open_modify_body_skel())
        controller.modifyBodyBtn.config(state="disabled")

        # buttons grid

        # controller.procesbtn.grid(row=1, column=1, sticky="nsew", pady = 5)
        # controller.modifybtn.grid(row=2, column=0, columnspan=2, sticky="nsew")

        controller.manual_imbtn.grid(row=1, column=0, columnspan=2, sticky="nsew", pady = 10)

        controller.lbl_cell_list.grid(row = 0, column = 0, sticky="nsew", pady = 10)
        controller.lbox.grid(row = 1, column = 0, rowspan = 4, sticky="nsew")

        controller.display_selectedbtn.grid(row = 5, column = 0, sticky="nsew")
        controller.modifyBodyBtn.grid(row=6, column=0, columnspan=2, sticky="nsew")