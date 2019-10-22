"""
Created on Tue Oct  9 16:37:02 2018

Module to modify the image processing process through a dedicated window in a GUI.

@author: Gabriele Nasello
"""

from tkinter import Toplevel

class ImModify():

    """
    Class that contains all the methods necessary to open a new window in a GUI
    and modify the image processising technique.
    """

    def __init__(self, parent, controller):

        self.parent = parent
        self.controller = controller

        controller.modifyWindow = Toplevel(controller.container)
        controller.modifyWindow.title(controller.interfacetitle + ' - Modify Image Processing')

        # button_panel = ModButtonPanel(self.container, controller=self)
        # self.im_panel = ModImagePanel(self.container, controller=self)