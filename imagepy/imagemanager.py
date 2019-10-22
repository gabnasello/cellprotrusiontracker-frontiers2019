# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 19:55:22 2018

Module to manage and to load microscope images in a GUI.

@author: Gabriele Nasello
"""

import matplotlib.figure as mplfig
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# in python 3.6 NavigationToolbar2TkAgg, in python 3.7 replace with NavigationToolbar2Tk
import pims.bioformats as pbf
import tkinter.filedialog as tkfd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
from tkinter import ttk  # https://docs.python.org/3/library/tkinter.ttk.html
import imagepy.imageprocesser as imp
import cv2

color = '#%02x%02x%02x' % (220,218,213) # background color of ttk widgets in Hex color format
plt.rcParams['figure.facecolor'] = color

class ImMan():
    
    """
    Class that contains all the methods necessary to load microscope images in a GUI.
    """    
    
    def __init__(self, parent, controller):
        """
        Initialize the object and create a blank starting image
        """
        
        self.controller = controller
        self.parent = parent
        self.imgfile = None # image file convert to a "pickable" format (see pbf2pickle class)

        self.imgsh = None # image showed in the GUI
        self.old_ix = None # old index for the slider
        
        self.fig = mplfig.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        
        left, width = .25, .5
        bottom, height = .25, .5
        right = left + width
        top = bottom + height
        
        c = [34 ,61, 113]
        c = [i/255 for i in c]
        self.ax.text(0.5 * (left + right), 0.5 * (bottom + top), 'ImagePy Project',
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=20, color = c,
                    transform=self.ax.transAxes)
        self.ax.axis('off')
        
        controller.canvas = FigureCanvasTkAgg(self.fig, master= self.parent)
        controller.canvas.draw()
        controller.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
    
    def load_images(self, imgfile = None):
        """
        Load the image that will be processed. 
        Image can be an original microscope image (ex. .nd2 format) or a generic image (ex. .tiff)
        Image metadata will be loaded if present.

        imgfile object is a pbf2pickle loaded in case a old project is opened
        """
        
        controller = self.controller

        if imgfile is None:
            # open a file chooser dialog and allow the user to select an input image
            path = tkfd.askopenfilename()

            # ensure a file path was selected
            if len(path) > 0:
                images = pbf.BioformatsReader(path)
                # sometimes it could be necessary to add ", java_memory='1024m'"
                self.imgfile = pbf2pickle(pbfimage=images)
            else:
                return
        else:
            # load pickle file
            self.imgfile = imgfile
            self.imgfile.print_image_info()

        self.ax.clear()
        self.ax.lines = []
        controller.canvas.draw()
        self.firstime = True
        self.add_slider()

        try:
            controller.toolbar
        except AttributeError:
            self.add_toolbar()

        controller.barON.set(0)

        if self.imgfile.dxyz is not None:
            controller.filemenu.showMenu.entryconfig(1, state='normal')
        else:
            controller.filemenu.showMenu.entryconfig(1, state='disabled')

        controller.manual_imbtn.config(state="normal")
        controller.filemenu.selectMenu.entryconfig(1, state='normal')
        controller.filemenu.selectMenu.entryconfig(2, state='normal')

        controller.lbl_cell_list.config(state="disabled")
        controller.cell_list.set('')
        controller.lbox.delete(0,'end')
        controller.lbox.config(state="disabled")

        controller.filemenu.fileMenu.entryconfig(3, state='normal')

        self.processed = imp.ImProcc(parent = self, controller = controller)

        self.plot_image()
            
    def plot_image(self):
        """
        Plot the loaded image in the imageHolder frame
        """        
        controller = self.controller
        
        if self.imgfile.shape[2] == 1:
            # images[0] timepoint 0
            # images[n][1,:,:] timepoint n, stack 1
            image = self.imgfile.imgdata[0][:, :]
            image = cv2.convertScaleAbs(image, alpha=(256.0 / self.imgfile.maxpixel))
            self.imgsh = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            self.ax.imshow(self.imgsh, cmap=plt.cm.gray)
                
        else:
            try:
                self.zframe_displ = round(controller.scrollbar.get())
            except AttributeError:
                self.zframe_displ = 0
            image = self.imgfile.imgdata[0][self.zframe_displ, :, :]
            image = cv2.convertScaleAbs(image, alpha = (256.0/self.imgfile.maxpixel))
            self.imgsh = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            if self.firstime:
                self.imshow = self.ax.imshow(self.imgsh, cmap=plt.cm.gray)
                self.firstime = False
            else:
                self.imshow.set_data(self.imgsh)
                
        self.ax.axis('off')

        if controller.roiON.get():
            self.processed.roi_selector()

        controller.canvas.draw()

    def add_toolbar(self):
        """
        Display a toolbar below the window
    
        """           
        
        controller = self.controller
        
        controller.toolbar = NavigationToolbar2Tk(controller.canvas, controller)
        controller.toolbar.update()
        
        controller.canvas._tkcanvas.grid(row=0, column=0,sticky="nsew")
        
    def add_slider(self):  
        """
        Display a slider below the image
        """        
        
        controller = self.controller
        
        im_idx = 0
        controller.scrollbar = ttk.Scale(controller.im_panel, from_=0, to=self.imgfile.shape[2]-1,
                                         orient="horizontal", command=lambda _: self.update_image_idx())
        #  focus_set method to move focus to a widget
        controller.scrollbar.focus_set()
        controller.scrollbar.set(im_idx)
        controller.scrollbar.grid(row=1, column=0, padx = 50, sticky="we")

        controller.scrollbarValue = ttk.Label(controller.im_panel, width = 5, text = 'Z : 1 ')
        controller.scrollbarValue.grid(row=1, column=1)

    def update_image_idx(self):
        """
        Function to check it the scrollbar value changed. If so, new image is plotted.
        """           
        
        controller = self.controller

        try:
            value = round(controller.scrollbar.get()) - self.old_ix
        except TypeError:
            value = 1
        
        if not(value == 0):

            self.plot_image()

            if controller.show_cellshapeON.get():
                controller.img.processed.show_cellprocessed()

            try:
                controller.scrollbarValue["text"] = 'Z : ' + str(round(controller.scrollbar.get()) + 1)
            except AttributeError:
                pass

        self.old_ix = round(controller.scrollbar.get())

    def add_scalebar(self):
        """
        Display a scale bar in a matplotlib figure
        """
        
        controller = self.controller
        
        if controller.barON.get():
            
            try:
                
                if self.imgfile.dxyz is not None:
                    scalebar = ScaleBar(self.imgfile.dxyz[0], units = self.imgfile.unit,
                                        frameon='False', color='w', location='lower right', 
                                        box_color='k', box_alpha='0')  
                    # 1 pixel = metadata info
                    self.ax.add_artist(scalebar)
                    controller.canvas.draw()

                    if controller.roiON.get():
                        self.processed.roi_selector()
                    
            except AttributeError:
                pass
        else:
            
            try:
                
                if self.imgfile.dxyz is not None:
                    self.ax.artists.clear()
                    self.fig.canvas.draw()
            
            except AttributeError:
                pass

class pbf2pickle():
    """
    Class that converts an image object loaded with the pims.bioformats module to
    an image object that can be handled by the pickle module.
    """

    def __init__(self, pbfimage):

        self.imgdata = [i for i in pbfimage]
        meta = pbfimage.metadata
        self.imgcount = meta.ImageCount()
        self.imgsize = pbfimage.sizes
        # self.shape image loaded size
        self.unit = None # metadata info, physical size unit
        self.dxyz = None # metadata info, pixel physical size
        self.volxyz = None # metadata info, volume physical size
        self.maxpixel = self.imgdata[0].max()
        self.minpixel = self.imgdata[0].min()

        if 'z' not in self.imgsize.keys():
            Zsize = 1
        else:
            Zsize = self.imgsize['z']

        self.shape = [self.imgsize['x'], self.imgsize['y'], Zsize]

        if 'Unit' in pbfimage.get_metadata_raw():
            self.unit = pbfimage.get_metadata_raw()['Unit']
            self.dxyz = [meta.PixelsPhysicalSizeX(0),
                    meta.PixelsPhysicalSizeY(0)]
            self.volxyz = [a * b for a, b in zip(self.dxyz, self.shape[0:2])]
            if 'z' in self.imgsize.keys():
                self.dxyz.append(meta.PixelsPhysicalSizeZ(0))
                self.volxyz.append(self.shape[2]*self.dxyz[2])

        print('\n%%%% NEW IMAGE LOADED%%%%')
        self.print_image_info()

    def print_image_info(self):

        print('\n---- IMAGE PARAMETERS ---')

        print('\nTimepoints imaged: {}'.format(self.imgcount))

        print('Image size: {} x {}'.format(*(self.imgsize['x'], self.imgsize['y'])))

        print('Z-stack images: {}'.format(self.shape[2]))

        if self.unit is not None:
            print('\nPixels Physical Size [', self.unit, ']')
            print(*np.around(self.dxyz, decimals=3), sep=' x ')

            print('\nImaged Surface/Volume Size [',self.unit,']')
            print(*np.around(self.volxyz, decimals=2), sep=' x ')