'''

Module to manually modify the cell body detection from the skeleton
through a dedicated window in a GUI.

Created by Gabriele Nasello on Nov 3 2018

'''

from copy import deepcopy
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure as mplfig
from tkinter import Toplevel
import tkinter as tk
from scipy.ndimage.measurements import label
from skimage.measure import regionprops
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import ttk  # https://docs.python.org/3/library/tkinter.ttk.html
from skimage.morphology import medial_axis, binary_dilation
import imagepy.skeletonprocessing as skpro

class CellBodyModify():
    """
    Class that contains all the methods necessary to manually modify the cell
    body detection from skeleton in a dedicated GUI window.
    """

    def __init__(self, img, cellshape, cellID, parent, controller):
        """
        Initialize the window with the image panel and buttons.
        """

        self.parent = parent
        self.controller = controller
        self.cellID = str(cellID)

        zframe = cellshape.zframe
        imgsh = img.imgfile.imgdata[0][zframe, :, :]

        controller.modifyWindow = Toplevel()
        controller.modifyWindow.title(controller.interfacetitle + ' - Manual Cell Body Detection')
        color = '#%02x%02x%02x' % (220, 218, 213)  # background color of ttk widgets in Hex color format
        controller.modifyWindow.configure(background = color)

        self.master = controller.modifyWindow

        self.im_manual_panel = ImManualPanel(imgsh, cellshape, parent = self, master = controller.modifyWindow)

        controller.modifyWindow.grid_columnconfigure(0, weight=20)
        controller.modifyWindow.grid_rowconfigure(0, weight=20)
        controller.modifyWindow.grid_rowconfigure(1, weight=1)

        self.im_manual_panel.grid(row=0, column=0, sticky="nsew")

    def saveclose(self):
        """
        Close the dedicated window and save manual selection.
        """
        master = self.master
        parent = self.parent
        controller = self.controller

        manpanel = self.im_manual_panel
        self.skelbody, self.skelprot = skpro.full_cell_skeletonization(manpanel.distmap, manpanel.thresh,
                                                                       manpanel.maxthre, manpanel.physpace)

        parent.shapecells[self.cellID].skelbody = self.skelbody
        parent.shapecells[self.cellID].skelprot = self.skelprot
        parent.shapecells[self.cellID].value = (str(np.around(parent.shapecells[self.cellID].contour['area'], decimals=1)),
                                                str(max(self.skelprot['protusion_id'])),
                                                ', '.join(str(np.around(len, decimals=1)) for len in self.skelprot['euclidean-length']))

        # plot modify skeletonization (if the proper z frame is showed)
        controller.show_cellshapeON.set(1)
        controller.img.processed.show_cellprocessed()

        master.withdraw()


class ImManualPanel(tk.Frame):
    """
    Class to initialize the image panel in a GUI window for manual cell body detection from skeleton.
    """

    def __init__(self, image, cellshape, parent, master):
        """
        Initialize image panel, loading the image associated to the cell body selected.
        """

        tk.Frame.__init__(self, master)
        color = '#%02x%02x%02x' % (220, 218, 213)  # background color of ttk widgets in Hex color format
        self.configure(background = color)

        self.parent = parent
        self.bodyimage = []

        image = image - np.min(image)
        imagescaled = cv2.convertScaleAbs(image, alpha=(255.0/(np.max(image))))

        self.skelbody = cellshape.skelbody
        self.maxthre = self.skelbody['maxthreshold']
        self.physpace = self.skelbody['physical-space']

        cellmask = cellshape.contour['mask']
        medialAxis, distance = medial_axis(cellmask, return_distance=True)
        self.distmap = np.array(distance * medialAxis)

        self.fig = mplfig.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.rgbimgsh = cv2.cvtColor(imagescaled,cv2.COLOR_GRAY2RGB)
        self.plot_body_skeleton(master=self.master)
        self.plot_cell_contour(cellshape)
        self.ax.axis('off')

        self.grid_columnconfigure(0, weight=10)
        self.grid_rowconfigure(0, weight=10)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        master.canvas = FigureCanvasTkAgg(self.fig, master = self)
        master.canvas.draw()
        master.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self.thresh = cellshape.skelbody['threshold']
        self.add_slider(self.thresh, master = self.master)

        master.save_btn = ttk.Button(self, text="Save and Quit", command = lambda: parent.saveclose())
        master.save_btn.grid(row=2, column=0, pady = 10)

    def plot_cell_contour(self, shapeobj):
        """
        Display cell contour in the modify window.
        """

        self.contourline = plt.Line2D(shapeobj.contour['allxpoints'] +
                                      [shapeobj.contour['allxpoints'][0]],
                                      shapeobj.contour['allypoints'] +
                                      [shapeobj.contour['allypoints'][0]],
                                      color=shapeobj.contour['color'])
        self.ax.add_line(self.contourline)

    def plot_body_skeleton(self, master):
        """
        Display cell skeleton in the modify window.
        """

        self.bodyimage = deepcopy(self.rgbimgsh)
        a = np.ones((4, 4))
        dilated = binary_dilation(self.skelbody['skeleton'], selem=a)
        rgbCol = (255,0,0)
        self.bodyimage[dilated, 0] = rgbCol[0]
        self.bodyimage[dilated, 1] = rgbCol[1]
        self.bodyimage[dilated, 2] = rgbCol[2]

        self.ax.imshow(self.bodyimage)

    def add_slider(self, inthr, master):
        """
        Display a slider below the image
        """

        master.scrollbar = ttk.Scale(self, from_=0, to=100,
                                     orient="horizontal", command=lambda _: self.update_threshold())
        #  focus_set method to move focus to a widget
        master.scrollbar.focus_set()
        master.scrollbar.set((1 - inthr/self.maxthre)*100)
        master.scrollbar.grid(row=1, column=0, padx=50, pady=10, sticky="we")

    def update_threshold(self):
        """
        Function to check it the scrollbar value changed to apply thresholding.
        :return:
        """

        master = self.master

        try:
            # round off until the first decimal place
            value = round(master.scrollbar.get()) - (1 - self.thresh/self.maxthre)*100
        except TypeError:
            value = 1

        if not(value == 0):

            self.thresh = (1 - round(master.scrollbar.get())/100) * self.maxthre

            self.skelbody['skeleton'] = self.cell_body_thresholding(self.distmap, self.thresh)
            self.plot_body_skeleton(master = self.master)
            master.canvas.draw()

    def cell_body_thresholding(self, distmap, threshold):
        """
        Apply manual thresholding to cell medial axis transform.
        :return:
        """
        BodyThreshInd = distmap < threshold
        distCellBody = deepcopy(distmap)
        distCellBody[BodyThreshInd] = 0

        # if more separate regions are selected, choose the longest one as cell body skeleton by label each separated region
        # and disacrding the shortest ones.
        structure = np.ones((3, 3), dtype=np.int)  # in this case we allow any kind of connection
        labeled, ncomponents = label(distCellBody, structure)
        regprop = regionprops(labeled)

        len_region = [i.perimeter for i in regprop]
        skelCellBody = labeled == (np.argmax(len_region) + 1)

        return skelCellBody