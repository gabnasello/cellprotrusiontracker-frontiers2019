"""
Created on Fri Oct  5 10:45:02 2018

Module to process microscope images in a GUI for cell dendrite tracking.

@author: Gabriele Nasello
"""

from matplotlib.widgets import RectangleSelector
from tkinter import messagebox
import imagepy.modifywindow as modw
import imagepy.manualselection as ms
import imagepy.printsummary as ps
import imagepy.skeletonprocessing as skpro
import imagepy.modifycellbody as modbody
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mplPath
from skimage.morphology import closing
from scipy.ndimage.measurements import label
import pandas as pd
from skimage.measure import regionprops
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
import cv2


class ImProcc():
    """
    Class that contains all the methods necessary to process microscope images in a GUI.
    """

    def __init__(self, parent, controller):
        """
        Initialize class.
        slef.click are the x, y coordinates of the low-left corner of the square roi.
        self.release are the x, y coordinates of the upright corner of the square roi.
        """
        self.click = [None, None]
        self.release = [None, None]

        self.image_roi = None

        self.parent = parent
        self.controller = controller

        self.shapecells = dict() # dictionary containing cell shape objects { Cell # : cell object }
        self.cell_zframes = dict()

        # panda DataFrame containing the cells connections and their coordinates
        row = ['zframe', 'cell1', 'cell2', 'centerX', 'centerY']
        data = np.empty((0, 5), int)
        self.connections = pd.DataFrame(data.tolist(), columns=row)

    def roi_selector(self):
        """
        Function to select the region of interest to process

        """

        controller = self.controller

        parent = self.parent

        def line_select_callback(eclick, erelease):
            'eclick and erelease are the press and release events'
            # if self.click[0] is None:
            #     controller.procesbtn.config(state="normal")
            #     controller.modifybtn.config(state="normal")

            self.click[:] = eclick.xdata, eclick.ydata
            self.release[:] = erelease.xdata, erelease.ydata
            self.controller.canvas.draw()

        if controller.roiON.get():
            self.RS = RectangleSelector(parent.ax, line_select_callback,
                                        drawtype='box', useblit=True,
                                        button=[1, 3],  # don't use middle button
                                        minspanx=5, minspany=5,
                                        spancoords='pixels',
                                        interactive=True)
            if self.click[0] is not None:
                self.RS.to_draw.set_visible(True)
                self.controller.canvas.draw()
                self.RS.extents = (self.click[0], self.release[0], self.click[1], self.release[1])
            else:
                self.controller.canvas.draw()

        else:

            try:
                self.RS.set_active(False)
                self.controller.canvas.draw()

            except AttributeError:
                pass

    def process_image(self):
        """
        Function to process the image of interest with default options.

        TO WRITE

        """

        parent = self.parent

        apply_threshold(self)

    def apply_threshold(self):
        """
        Function to apply image threshold.

        TO WRITE

        """

        if self.click[0] is None:
            messagebox.showerror("Error", "Select a ROI to process")
        else:
            parent = self.parent
            if parent.shape[2] == 1:
                # images[0] timepoint 0
                # images[n][1,:,:] timepoint n, stack 1
                self.image_roi = parent.file[0][self.click[1]:self.release[1], self.click[0]:self.release[0]]
            else:
                frame_displ = round(controller.scrollbar.get())
                self.image_roi = parent.file[0][frame_displ, self.click[1]:self.release[1],
                                 self.click[0]:self.release[0]]

    def open_modify(self):
        """
        Function to initialize the window to modify the image processing.
        """

        self.modproc = modw.ImModify(parent=self, controller=self.controller)

    def open_modify_body_skel(self):
        """
        Function to initialize the window to modify the cell body skeleton detection.
        """

        controller = self.controller
        try:
            cell_id = controller.lbox.curselection()[0] + 1

            self.modcellbody = modbody.CellBodyModify(img = self.parent, cellshape = self.shapecells[str(cell_id)],
                                                      cellID = cell_id, parent=self, controller=self.controller)
        except IndexError:

            messagebox.showerror("Error", "Select a cell to modify from the list and press again the button.")


    def manual_selector(self):
        """
        Function to initialize the window to manually select cell contour.
        """

        self.cellobject = singleCellShape(parent = self, controller = self.controller) # object with single cell contour
        self.manselec = ms.ManualSelector(img = self.parent, parent = self, controller = self.controller)

    def create_cell_list(self, procfile):
        """
        Function to crete the list of cell processed to show in the listbox of the main GUI window.
        This function is called when a file project is loaded
        """

        self.shapecells = procfile['shapecells']
        self.cell_zframes = procfile['cell_zframes']
        self.connections = procfile['connections']

        for i in self.shapecells.keys():
            self.add_item_cell_list(int(i))

    def add_item_cell_list(self, idx):
        """
        Function to update the list of cell processed to show in the listbox of the main GUI window.
        """
        controller = self.controller

        if idx == 1:
            # turno on buttons
            controller.lbl_cell_list.config(state="normal")
            controller.lbox.config(state="normal")
            controller.filemenu.showMenu.entryconfig(2, state='normal')
            controller.show_cellshapeON.set(1)
            controller.display_selectedbtn.config(state="normal")
            controller.filemenu.summaryMenu.entryconfig(1, state='normal')
            controller.filemenu.summaryMenu.entryconfig(2, state='normal')
            controller.modifyBodyBtn.config(state="normal")

            #  focus_set method to move focus back to the scrollbar of the mainGUI
            controller.scrollbar.focus_set()

        controller.lbox.insert(tk.END, 'Cell # ' + str(idx))
        color = '#%02x%02x%02x' % tuple([int(i * 255) for i in self.shapecells[str(idx)].contour['color']]) # Hex color format
        controller.lbox.itemconfig(idx-1, {'fg': color})

    def cbtn_show_cellprocessed(self):
        """
        Function connect to controller.cbtn_showcell checkbutton
        to show cell shape processed on the main GUI window.
        """

        controller = self.controller

        if controller.show_cellshapeON.get():
            self.show_cellprocessed()
        else:
            controller.img.ax.lines = []
            controller.canvas.draw()

    def display_single_cell_processing(self, shapeobj, **linekwargs):
        """
        Display cell contour in the canvas of the main GUI window.
        """
        controller = self.controller
        l = plt.Line2D(shapeobj.contour['allxpoints'] +
                       [shapeobj.contour['allxpoints'][0]],
                       shapeobj.contour['allypoints'] +
                       [shapeobj.contour['allypoints'][0]],
                       color=shapeobj.contour['color'], **linekwargs)
        controller.img.ax.add_line(l)

    def display_single_cell_skeleton(self, shapeobj, **linekwargs):
        """
        Display cell skeleton in the canvas of the main GUI window.
        """
        controller = self.controller

        color_cellbody = '#ff0000'
        for path in shapeobj.skelbody['paths']:
            l = plt.Line2D(path[:, 1], path[:, 0], color = color_cellbody, **linekwargs)
            controller.img.ax.add_line(l)

        color_secondary = '#ffffff'  # '#ffc03e'
        for protusion in shapeobj.skelprot['secondary-paths']:
            for path in protusion:
                l = plt.Line2D(path[:, 1], path[:, 0], color=color_secondary, **linekwargs)
                controller.img.ax.add_line(l)

        # color = '#FFC125'
        color_primary = '#ffff00'
        for path in shapeobj.skelprot['primary-path']:
            l = plt.Line2D(path[:, 1], path[:, 0], color=color_primary, **linekwargs)
            controller.img.ax.add_line(l)

    def display_cell_connections(self, connobj):
        """
        Display cell connections in the canvas of the main GUI window.
        """
        controller = self.controller
        rgbCol = (1, 0, 0)  # red
        patches = []
        coord = np.array([connobj.centerX.tolist(), connobj.centerY.tolist()]).transpose()
        coord = tuple(map(tuple, coord))
        for c in coord:
            circle = Circle(c, radius=15)
            patches.append(circle)
        connectCollection = PatchCollection(patches, facecolors=rgbCol)
        controller.img.ax.add_collection(connectCollection)


    def show_cellprocessed(self):
        """
        Function to activate cell processed visualization in the main GUI window.
        """

        controller = self.controller

        controller.img.ax.lines = []
        controller.img.ax.collections = []

        zframe = round(controller.scrollbar.get())

        if str(zframe) in self.cell_zframes.keys():

            for nroi in self.cell_zframes[str(zframe)]:
                self.display_single_cell_processing(shapeobj= self.shapecells[str(nroi)])
                self.display_single_cell_skeleton(shapeobj= self.shapecells[str(nroi)])
            self.display_cell_connections(connobj = self.connections[self.connections.zframe == zframe])

        else:
            pass
        controller.canvas.draw()


    def display_cell_selected(self):
        """
        Function to change the image zframe visualized in the main GUI window to the one of the cell selected
        in the listbox
        """

        controller = self.controller
        try:
            cell_id = controller.lbox.curselection()[0] + 1
            im_idx = self.shapecells[str(cell_id)].zframe

            controller.scrollbar.set(im_idx)
            controller.show_cellshapeON.set(1)
            self.show_cellprocessed()
        except IndexError:
            messagebox.showerror("Error", 'Select a cell to show from the ''Cell Processed List'' and press again the button.')


    def print_summary(self):
        """
        Function to start the visualization and further saving of the parameters extracted by cell shape
        """

        controller = self.controller

        ps.PrintParameters(parent = self, controller = controller)



class singleCellShape():
    """
    Class that manages cell contours processed in the GUI.
    """
    def __init__(self, parent, controller):
        """
        Initialize class.
        slef.click are the x, y coordinates of the low-left corner of the square roi.
        self.release are the x, y coordinates of the upright corner of the square roi.
        """
        self.parent = parent
        self.controller = controller

        self.zframe = []  # list containing cell shape location in the z-stack
        self.contour = {'allxpoints': [], 'allypoints': [], 'color': 'r', 'area': [], 'mask': []}
        # dictionary containing data about cell boundary and the associated mask

        self.skeleton = skpro.SkelProc(parent = self, controller = controller)

        # # array containing the cellID to which the processed cell connects
        # self.connections = np.empty((0), int)

    def save_shape(self, xdata, ydata, zframe):
        """
        Save cell contour data (from automatic processing or manual selection) to an
        element of the singleCellShape object (from parent)
        """

        controller = self.controller
        parent = self.parent

        self.contour['allxpoints'] = xdata
        self.contour['allypoints'] = ydata
        self.measure_area()

        mask = closing(self.getMask(cv2.cvtColor(controller.img.imgsh, cv2.COLOR_BGR2GRAY)))
        # sometimes maskig creates separate regions. The following lines select the biggest one
        structure = np.ones((3, 3), dtype=np.int)  # in this case we allow any kind of connection
        labeled, ncomponents = label(mask, structure)
        regprop = regionprops(labeled)
        area = []
        for r in regprop:
            area.append(r.area)
        self.contour['mask'] = labeled == np.array(area).argmax()+1
        self.zframe = zframe


        cmap_name = 'Set1'
        cmap = plt.get_cmap(cmap_name)

        try:
            last_id = sorted(list(map(int,parent.shapecells.keys())))[-1]
            cell_id = last_id + 1
        except IndexError:
            cell_id = 1

        color_id = (cell_id) % 7  # 8 is the numbers of colors in the Set1 colormap
        self.contour['color'] = cmap.colors[color_id]

        try:
            self.skeleton.skletonize_cell(cellmask = self.contour['mask'])
        except IndexError:
            print('\n\n%%%%%%%ERROR%%%%%%%%%\n\n')
            self.skeleton = []
            pass

        self.check_cell_connections(cellmask=self.contour['mask'], cellprocessID = cell_id)

        parent.shapecells[str(cell_id)] = storeProcessedAspickle(cellshapeobj = self)

        try:
            parent.cell_zframes[str(self.zframe)].append(cell_id)
        except KeyError:
            parent.cell_zframes[str(self.zframe)] = [cell_id]

        parent.add_item_cell_list(idx = cell_id)
        controller.show_cellshapeON.set(1)
        parent.show_cellprocessed()


    def check_cell_connections(self, cellmask, cellprocessID):
        """
        Determine cell connections with the other cells selected on the same frame.
        """
        zframe = self.zframe
        parent = self.parent

        if str(zframe) in parent.cell_zframes.keys():

            for cellID in parent.cell_zframes[str(zframe)]:
                # check intersections between processed cell mask and one of a cell already processed on the same z frame
                mask = cellmask.astype(int) + parent.shapecells[str(cellID)].contour['mask'].astype(int)
                mask = mask > 1

                structure = np.ones((3, 3), dtype=np.int)  # in this case we allow any kind of connection
                # in case there more connections between the same cells
                labeled, nconnections = label(mask, structure)

                regprop = regionprops(labeled)

                for r in regprop:
                    center = np.array(r.centroid).astype(int).tolist()
                    data = [zframe, cellprocessID, cellID, center[1], center[0]]
                    frameRow = pd.DataFrame([data], columns = list(parent.connections))
                    parent.connections = parent.connections.append(frameRow, ignore_index=True)

                # # store connection data in the cell object under process
                # self.connections = np.append(self.connections, np.array([cellID] * nconnections).astype(int), axis = 0)
                #
                # # store connection data in the cell object already processed
                # parent.shapecells[str(cellID)].connections = np.append(parent.shapecells[str(cellID)].connections,
                #                                                        np.array([cellprocessID] * nconnections).astype(int),
                #                                                        axis=0)

    def getMask(self, currentImage):
        """
        Create the cell image mask from the cell boundary.
        """
        ny, nx = np.shape(currentImage)
        poly_verts = [(self.contour['allxpoints'][0], self.contour['allypoints'][0])]
        for i in range(len(self.contour['allxpoints']) - 1, -1, -1):
            poly_verts.append((self.contour['allxpoints'][i], self.contour['allypoints'][i]))

        # Create vertex coordinates for each grid cell...
        # (<0,0> is at the top left of the grid in this system)
        x, y = np.meshgrid(np.arange(nx), np.arange(ny))
        x, y = x.flatten(), y.flatten()
        points = np.vstack((x, y)).T

        ROIpath = mplPath.Path(poly_verts)

        return ROIpath.contains_points(points).reshape((ny, nx))

    def measure_area(self):

        """
        Measure cell area from its contour
        """

        controller = self.controller

        x = self.contour['allxpoints']
        y = self.contour['allypoints']
        self.contour['area'] = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

        physical_size = controller.img.imgfile.dxyz # metadata info, pixel physical size (see imagemanager
        if physical_size is not None:
            self.contour['area'] = self.contour['area'] / (physical_size[0] * physical_size[1])

class storeProcessedAspickle():
    """
    Class to store all attributes of the singleCellShape class in an object without methods or tkinker reference,
    thus "picklable".
    """

    def __init__(self, cellshapeobj):
        """
        Initialize class, copying all attributes from singleCellShape object.
        """
        self.zframe = cellshapeobj.zframe  # list containing cell shape location in the z-stack
        self.contour = cellshapeobj.contour # cell contour dictionary

        try:
            self.skelbody = cellshapeobj.skeleton.skelbody # cell body skeleton dictionary
            self.skelprot = cellshapeobj.skeleton.skelprot  # cell protusions skeleton dictionaryç
        except AttributeError:
            pass

        #self.connections = cellshapeobj.connections