import tkinter as tk
from tkinter import ttk  # https://docs.python.org/3/library/tkinter.ttk.html

import imagepy.imagemanager as imm
import imagepy.guipanels as gp
import imagepy.menubarhandle as mbh

# A java virtual machine needs to be initialized the first time the code is tun in a new device
# startJVM(getDefaultJVMPath(), "-ea") 
# import jpype
# if jpype.isJVMStarted():
#     jpype.startJVM(jpype.getDefaultJVMPath(), "-ea")


class ImagePyGUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.interfacetitle = ('ImagePy')
        self.title(self.interfacetitle + ' - Main')

        self.container = tk.Frame(self, background="bisque")
        self.container.pack(fill="both", expand=True)
        
        self.container.style = ttk.Style()
        self.container.style.theme_use("clam")

        button_panel = gp.ButtonPanel(self.container, controller=self)
        self.im_panel = gp.ImagePanel(self.container, controller=self)

        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=20)
        self.container.grid_rowconfigure(0, weight=1)

        button_panel.grid(row=0, column=0, sticky="nsew")
        self.im_panel.grid(row=0, column=1, sticky="nsew")

        self.img = imm.ImMan(parent = self.im_panel, controller = self)

        self.filemenu = mbh.MenuWindow(self.container, controller=self)


interface = ImagePyGUI()
interface.minsize(800, 480)
interface.mainloop()