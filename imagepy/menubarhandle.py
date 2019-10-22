'''

Module to manage the menu bar in the main GUI window

Created by Gabriele Nasello on Oct 16 2018

'''

import tkinter as tk
import tkinter.filedialog as tkfd
import pickle as pk
from imagepy.printsummary import save_excel_tab

# Here, we are creating our class, Window, and inheriting from the tk. Frame
# class.
class MenuWindow(tk.Frame):
    """
    Class that file menu window in the main GUI to load and save processed data
    """

    # . Here you can specify
    def __init__(self, parent, controller):
        """
        Define settings upon initialization
        """
        # parameters that you want to send through the Frame class.
        tk.Frame.__init__(self, parent)

        # reference to the controller widget, which is the tk window
        self.controller = controller

        # creating a menu instance
        self.menu = tk.Menu(controller)

        color = '#%02x%02x%02x' % (226,224,220) # background color of ttk widgets in Hex color format
        self.menu.configure(background = color)
        controller.config( menu = self.menu)

        # create the file object)
        self.fileMenu = tk.Menu(self.menu)

        # adds a command to the menu option, calling it exit, and the
        # command it runs on event is client_exit
        self.fileMenu.add_command(label="New Analysis", command = controller.img.load_images)
        self.fileMenu.add_command(label="Load Analysis", command = self.loadpicklefile)
        self.fileMenu.add_command(label="Save Analysis", command=self.savefile)
        self.fileMenu.entryconfig(3, state='disabled')

        # added "file" to our menu
        self.menu.add_cascade(label="File", menu=self.fileMenu)

        # create "show" menu
        self.selectMenu = tk.Menu(self.menu)
        controller.roiON = tk.IntVar()
        self.selectMenu.add_checkbutton(label="ROI selector", variable=controller.roiON,
                                        command = lambda: controller.img.processed.roi_selector())

        self.selectMenu.add_command(label="Manual Selector",
                                    command = lambda: controller.img.processed.manual_selector())
        self.selectMenu.entryconfig(1, state='disabled')
        self.selectMenu.entryconfig(2, state='disabled')
        self.menu.add_cascade(label='Select', menu=self.selectMenu)

        # create "show" menu
        self.showMenu = tk.Menu(self.menu)
        controller.barON = tk.IntVar()
        self.showMenu.add_checkbutton(label="Scalebar", variable=controller.barON, command = lambda: controller.img.add_scalebar())

        controller.show_cellshapeON = tk.IntVar()
        self.showMenu.add_checkbutton(label="Show Cell Processed", variable=controller.show_cellshapeON, command = lambda: controller.img.processed.cbtn_show_cellprocessed())
        self.showMenu.entryconfig(1, state='disabled')
        self.showMenu.entryconfig(2, state='disabled')
        self.menu.add_cascade(label='Show', menu=self.showMenu)

        self.summaryMenu = tk.Menu(self.menu)
        self.summaryMenu.add_command(label="Print Summary",
                                    command = lambda: controller.img.processed.print_summary())
        self.summaryMenu.add_command(label="Save Summary",
                                    command = lambda: save_excel_tab(controller = controller))
        self.summaryMenu.entryconfig(1, state='disabled')
        self.summaryMenu.entryconfig(2, state='disabled')
        self.menu.add_cascade(label='Summary', menu=self.summaryMenu)


    def loadpicklefile(self):
        """
        Load a processed image in pickle format
        """

        path = tkfd.askopenfilename(filetypes=[("Pickle files (*.pk *.pickle)", "*.pk; *.pickle")])

        if len(path) == 0:  # asksaveasfile return `None` if dialog closed with "cancel".
            return

        controller = self.controller

        with open(path, 'rb') as f:
            dictload = pk.load(f)

        imgfile = dictload['imgfile']
        controller.img.load_images(imgfile = imgfile)

        if dictload['shapecells'] != {}:
            controller.img.processed.create_cell_list(procfile = dictload)
            controller.img.processed.show_cellprocessed()

    def savefile(self):
        """
        Save a processed image in pickle format
        """

        controller = self.controller

        # if controller.img.imgfile is None:
        #     messagebox.showinfo("No Image", "Please load an image and later save the project")
        # else:
        path = tkfd.asksaveasfilename(defaultextension=".pk", filetypes=[("Pickle files (*.pk)", "*.pk ")])
        if len(path) == 0:  # asksaveasfile return `None` if dialog closed with "cancel".
            return

        self.data_save = dict(imgfile = controller.img.imgfile,
                              shapecells = controller.img.processed.shapecells,
                              cell_zframes = controller.img.processed.cell_zframes,
                              connections = controller.img.processed.connections)

        with open(path, 'wb') as f:
            pk.dump(self.data_save, f)