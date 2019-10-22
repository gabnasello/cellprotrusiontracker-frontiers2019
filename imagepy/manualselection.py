'''

Module to manually select a contour through a dedicated window in a GUI.

Created by Gabriele Nasello on Oct 12 2018

'''


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure as mplfig
from tkinter import Toplevel
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# in python 3.6 NavigationToolbar2TkAgg, in python 3.7 replace with NavigationToolbar2Tk
from tkinter import ttk  # https://docs.python.org/3/library/tkinter.ttk.html

class ManualSelector():
    """
    Class that contains all the methods necessary to manually select a region of interest (ROI) in a dedicated GUI window.
    """

    def __init__(self, img, parent, controller):
        """
        Initialize the window with button and image panel.
        """

        self.parent = parent
        self.controller = controller

        self.roip = None # polygonal region of interest object (manually selected)

        self.zframe = img.zframe_displ

        controller.modifyWindow = Toplevel()
        controller.modifyWindow.title(controller.interfacetitle + ' - Manual Selection Tool')

        self.master = controller.modifyWindow

        self.im_manual_panel = ImManualPanel(img, master = controller.modifyWindow, controller = controller)
        self.btn_manual_panel = BtnManualPanel(parent = self, master = controller.modifyWindow)

        controller.modifyWindow.grid_columnconfigure(0, weight=20)
        controller.modifyWindow.grid_columnconfigure(1, weight=1)
        controller.modifyWindow.grid_rowconfigure(0, weight=20)
        controller.modifyWindow.grid_rowconfigure(1, weight=1)

        self.im_manual_panel.grid(row=0, column=0, sticky="nsew")
        self.btn_manual_panel.grid(row=0, column=1, sticky="nsew")

        self.add_toolbar(master = controller.modifyWindow)

    def saveclose(self):
        """
        Close the dedicated window and save manual selection.
        """

        parent = self.parent
        controller = self.controller

        parent.cellobject.save_shape(xdata = self.roip.allxpoints, ydata = self.roip.allypoints,
                                     zframe = self.zframe)

        controller.modifyWindow.withdraw()

    def add_toolbar(self, master):
        """
        Display a toolbar below the window.
        """

        master.toolbarFrame = tk.Frame(master = master)
        master.toolbarFrame.grid(row=1, column=0, columnspan = 2, sticky="nsew")
        master.toolbar = NavigationToolbar2Tk(master.canvas, master.toolbarFrame)
        master.toolbar.update()

    def start_roip(self):
        """
        Start the manual selection process.
        """

        self.roip = RoiPol(self, roicolor='r', controller = self.controller)

        self.im_manual_panel.lbl_click['text'] = 'Left Click: line segment\t\tRight Click: close region'

        self.btn_manual_panel.start_roi_btn.config(state="disabled")
        self.btn_manual_panel.clear_btn.config(state="normal")



class ImManualPanel(tk.Frame):
    """
    Class to initialize an image panel in a GUI window for manual ROI selection.
    """

    def __init__(self, image, master, controller):
        """
        Initialize image panel, loading the image showed in the main window
        """
        self.controller = controller
        self.master = master

        tk.Frame.__init__(self, master)
        color = '#%02x%02x%02x' % (220, 218, 213)  # background color of ttk widgets in Hex color format
        self.configure(background = color)

        self.fig = mplfig.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.imshow(image.imgsh, cmap=plt.cm.gray)
        self.ax.axis('off')

        self.plot_processed_cells(image.zframe_displ)

        self.grid_columnconfigure(0, weight=10)
        self.grid_rowconfigure(0, weight=10)
        self.grid_rowconfigure(1, weight=1)

        master.canvas = FigureCanvasTkAgg(self.fig, master=self)
        master.canvas.draw()
        master.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self.lbl_click = ttk.Label(self, text='ImagePy - Manual Selector Tool', font=("Arial", 10, "bold"))
        self.lbl_click.grid(row=1, column=0, sticky="we", padx = 50, pady = 10)
        self.lbl_click.configure(anchor="center")

    def plot_processed_cells(self, zframe):
        """
        show processed cell in the current z-frame
        """
        master = self.master
        controller = self.controller
        shapecells = controller.img.processed.shapecells
        cell_zframes = controller.img.processed.cell_zframes

        if str(zframe) in cell_zframes.keys():

            for nroi in cell_zframes[str(zframe)]:
                self.plot_single_cell_processing(shapeobj=shapecells[str(nroi)])
                self.plot_single_cell_skeleton(shapeobj=shapecells[str(nroi)])
        else:
            pass

    def plot_single_cell_processing(self, shapeobj, **linekwargs):
        """
        Display cell contour canvas of the Manual Selection GUI window.
        """
        l = plt.Line2D(shapeobj.contour['allxpoints'] +
                       [shapeobj.contour['allxpoints'][0]],
                       shapeobj.contour['allypoints'] +
                       [shapeobj.contour['allypoints'][0]],
                       color=shapeobj.contour['color'], **linekwargs)
        self.ax.add_line(l)

    def plot_single_cell_skeleton(self, shapeobj, **linekwargs):
        """
        Display cell skeleton in the canvas of the Manual Selection GUI window.
        """

        color_cellbody = '#ff0000'
        for path in shapeobj.skelbody['paths']:
            l = plt.Line2D(path[:, 1], path[:, 0], color = color_cellbody, **linekwargs)
            self.ax.add_line(l)

        color_secondary = '#ffffff'  # '#ffc03e'
        for protusion in shapeobj.skelprot['secondary-paths']:
            for path in protusion:
                l = plt.Line2D(path[:, 1], path[:, 0], color=color_secondary, **linekwargs)
                self.ax.add_line(l)

        # color = '#FFC125'
        color_primary = '#ffff00'
        for path in shapeobj.skelprot['primary-path']:
            l = plt.Line2D(path[:, 1], path[:, 0], color=color_primary, **linekwargs)
            self.ax.add_line(l)


class BtnManualPanel(tk.Frame):
    """
    Class to initialize a button panel in a GUI window for manual ROI selection.
    """

    def __init__(self, parent, master):
        """
        Initialize button panel
        """

        tk.Frame.__init__(self, master)
        color = '#%02x%02x%02x' % (220, 218, 213)  # background color of ttk widgets in Hex color format
        self.configure(background = color)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.start_roi_btn = ttk.Button(self, text="Start Manual Selection", command = lambda: parent.start_roip())
        self.start_roi_btn.grid(row=0, column=0, pady = 10)

        self.clear_btn = ttk.Button(self, text="Clear Last Segment", command = lambda: parent.roip.clear_segment())
        self.clear_btn.grid(row=1, column=0, pady = 10)
        self.clear_btn.config(state = 'disabled')

        master.save_btn = ttk.Button(self, text="Save and Quit", command = lambda: parent.saveclose())
        master.save_btn.grid(row=2, column=0, pady = 10)
        master.save_btn.config(state = 'disabled')

class RoiPol:
    '''Draw polygon regions of interest (ROIs) in matplotlib images,
    similar to Matlab's roipoly function.

    See the file example.py for an application.

    Created by Joerg Doepfert 2014 based on code posted by Daniel
    Kornhauser.
    '''

    def __init__(self, parent, controller, roicolor='b'):

        self.previous_point = []
        self.allxpoints = []
        self.allypoints = []
        self.start_point = []
        self.end_point = []
        self.line = None
        self.roicolor = roicolor
        self.fig = parent.im_manual_panel.fig
        self.ax = parent.im_manual_panel.ax
        self.master = parent.master
        self.closedpoly = False

        self.controller = controller

        self.__ID1 = self.fig.canvas.mpl_connect(
            'motion_notify_event', self.__motion_notify_callback)
        self.__ID2 = self.fig.canvas.mpl_connect(
            'button_press_event', self.__button_press_callback)

    def __motion_notify_callback(self, event):
        if event.inaxes:
            ax = event.inaxes
            x, y = event.xdata, event.ydata
            if (event.button == None or event.button == 1) and self.line != None:  # Move line around
                self.line.set_data([self.previous_point[0], x],
                                   [self.previous_point[1], y])
                self.fig.canvas.draw()

    def clear_segment(self):
        """
        Clear the last line segment created
        """

        if self.closedpoly: # if the button is pressed after closing the polygon
            del (self.ax.lines[-1])
            self.__ID1 = self.fig.canvas.mpl_connect(
                'motion_notify_event', self.__motion_notify_callback)
            self.__ID2 = self.fig.canvas.mpl_connect(
                'button_press_event', self.__button_press_callback)
            self.fig.canvas.draw()
            self.closedpoly = False
            self.master.save_btn.config(state='disabled')
        else:
            try:
                del (self.ax.lines[-2])
                self.previous_point = [self.allxpoints[-2], self.allypoints[-2]]
                del (self.allxpoints[-1])
                del (self.allypoints[-1])

            except IndexError:
                try: # to avoid IndexError if the user press the "Clear Last Segment" button before drawing
                    del (self.ax.lines[-1])
                    del (self.start_point)
                    self.line = None
                    self.fig.canvas.draw()
                except IndexError:
                    pass


    def __button_press_callback(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            ax = event.inaxes
            if event.button == 1 and event.dblclick == False:  # If you press the left button, single click
                if self.line == None:  # if there is no line, create a line
                    self.line = plt.Line2D([x, x],
                                           [y, y],
                                           marker='o',
                                           color=self.roicolor)
                    self.start_point = [x, y]
                    self.previous_point = self.start_point
                    self.allxpoints = [x]
                    self.allypoints = [y]

                    ax.add_line(self.line)
                    self.fig.canvas.draw()
                    # add a segment
                else:  # if there is a line, create a segment
                    self.line = plt.Line2D([self.previous_point[0], x],
                                           [self.previous_point[1], y],
                                           marker='o', color=self.roicolor)
                    self.previous_point = [x, y]
                    self.allxpoints.append(x)
                    self.allypoints.append(y)

                    event.inaxes.add_line(self.line)
                    self.fig.canvas.draw()
            elif ((event.button == 1 and event.dblclick == True) or
                  (
                          event.button == 3 and event.dblclick == False)) and self.line != None:  # close the loop and disconnect
                self.fig.canvas.mpl_disconnect(self.__ID1)  # joerg
                self.fig.canvas.mpl_disconnect(self.__ID2)  # joerg

                self.line.set_data([self.previous_point[0],
                                    self.start_point[0]],
                                   [self.previous_point[1],
                                    self.start_point[1]])
                ax.add_line(self.line)
                self.fig.canvas.draw()
                self.closedpoly = True
                self.master.save_btn.config(state='normal')