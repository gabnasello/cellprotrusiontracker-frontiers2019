'''

Module to visualized parameters of cell shape in a dedicated window and save
these data in a .cvs file

Created by Gabriele Nasello on Oct 12 2018

'''

from tkinter import Toplevel
from tkinter import ttk
from tkinter import Label
import tkinter as tk
import pandas as pd
import numpy as np
import tkinter.filedialog as tkfd


def save_excel_tab(controller):
    """
    Save cell shape parameters in a csv file. Cells shape data are stored in a dictionary.
    """

    unit = controller.img.imgfile.unit  # metadata info, physical size unit (see imagemanager module)

    if unit is None:
        unit = 'pixel'

    shapecells = controller.img.processed.shapecells
    protDataFrame = protusion_tab(shapecells)
    protDataFrame.columns = ['Cell #',
                          'Cell Area' + ' [' + unit + '\u00B2]',
                          '# Prim. Prot.',
                          'Prim. Prot. Lengths' + ' [' + unit + ']']

    connectionsDataFrame = controller.img.processed.connections
    connectionsDataFrame.columns = ['Z Frame',
                          '# Cell 1',
                          '# Cell 2',
                          'Center X',
                          'Center Y']

    imgfile = controller.img.imgfile
    dataimgSize = {'Timepoints' : [imgfile.imgcount],
            'Image Size - X' : [imgfile.imgsize['x']],
            'Image Size - Y': [imgfile.imgsize['y']],
            'Z-stack Frames' : [imgfile.shape[2]],
            'Unit': [unit]}
    try:
        dataimgSize['Pixels Physical Size - X'] = [imgfile.dxyz[0]]
        dataimgSize['Pixels Physical Size - Y'] = [imgfile.dxyz[1]]
        dataimgSize['Imaged Volume Size - X'] = [imgfile.volxyz[0]]
        dataimgSize['Imaged Volume Size - Y'] = [imgfile.volxyz[1]]
    except AttributeError:
        dataimgSize['Pixels Physical Size - X'] = [np.nan]
        dataimgSize['Pixels Physical Size - Y'] = [np.nan]
        dataimgSize['Imaged Volume Size - X'] = [np.nan]
        dataimgSize['Imaged Volume Size - Y'] = [np.nan]

    try:
        dataimgSize['Pixels Physical Size - Z'] = [imgfile.dxyz[2]]
        dataimgSize['Imaged Volume Size - Z'] = [imgfile.volxyz[2]]
    except AttributeError:
        dataimgSize['Pixels Physical Size - Z'] = [np.nan]
        dataimgSize['Imaged Volume Size - Z'] = [np.nan]

    imgsizeDataFrame = pd.DataFrame(data = dataimgSize)

    path = tkfd.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files (*.xlsx)", "*.xlsx ")])
    if len(path) == 0:  # asksaveasfile return `None` if dialog closed with "cancel".
        return

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(path, engine='xlsxwriter')

    # Convert the dataframe to an XlsxWriter Excel object.
    protDataFrame.to_excel(writer, sheet_name='Cells Protusions')
    connectionsDataFrame.to_excel(writer, sheet_name='Cells Connections')
    imgsizeDataFrame.to_excel(writer, sheet_name='Imaged Size')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

def protusion_tab(shapecells):
    """
    Create the updated protusion tab.
         Insert some rows
         define the array that will be than showed in the print summary window (see module)
         list of values:
         cell  area
         number of primary protusions
         length of each primary protusion
         connecting cells
    """
    row = ['cell#', 'area', 'protusion_id', 'euclidean-length']
    emptydata = np.empty((0, 5), int)
    protTab = pd.DataFrame(emptydata.tolist(), columns=row)
    for i in shapecells.keys():
        rowFrame = [int(i),
                np.around(shapecells[i].contour['area'], decimals=1),
                max(shapecells[i].skelprot['protusion_id']),
                0]
        cellRow = pd.DataFrame([rowFrame], columns=list(protTab))
        cellRow.loc[[0], row[-1]] = pd.Series([[np.around(len, decimals=1) for len in shapecells[i].skelprot['euclidean-length']]])
        protTab = protTab.append(cellRow, ignore_index=True)

    return protTab

class PrintParameters(tk.Frame):
    """
    Class that contains all the methods necessary to visualize cell shape parameters in a dedicated window.
    """

    def __init__(self, parent, controller):
        """
        Initialize the window with treeview (summary table) and buttons
        """
        self.parent = parent
        self.controller = controller

        controller.printWindow = Toplevel()
        controller.printWindow.title(controller.interfacetitle + ' - Print Summary')

        self.master = controller.printWindow

        protusionlabel = Label(master = self.master, text='Cells Protusions Tab', font=(14), pady = 5)
        self.tableProtusionSummary = TabProtusionSummary(data = parent.shapecells, master = self.master, controller = controller)

        connectionlabel = Label(master = self.master, text='Cells Connections Tab', font=(14), pady = 5)
        self.tableConnectionSummary = TabConnectionSummary(data = parent.connections, master = self.master, controller = controller)

        imsizelabel = Label(master=self.master, text='Imaged Size Tab', font=(14), pady = 5)
        self.imSizeSummary = TabImageSizeSummary(imgfile = controller.img.imgfile, master = self.master, controller = controller)

        controller.printWindow.grid_columnconfigure(0, weight=20)
        controller.printWindow.grid_columnconfigure(1, weight=1)
        controller.printWindow.grid_rowconfigure(0, weight=1)
        controller.printWindow.grid_rowconfigure(1, weight=20)
        controller.printWindow.grid_rowconfigure(2, weight=1)
        controller.printWindow.grid_rowconfigure(3, weight=20)
        controller.printWindow.grid_rowconfigure(4, weight=1)
        controller.printWindow.grid_rowconfigure(5, weight=20)

        protusionlabel.grid(row=0, column=0, columnspan = 2, sticky="nsw")
        self.tableProtusionSummary.grid(row=1, column=0, columnspan = 2, sticky="nsew")

        connectionlabel.grid(row=2, column=0, columnspan = 2, sticky="nsw")
        self.tableConnectionSummary.grid(row=3, column=0, columnspan = 2, sticky="nsew")

        imsizelabel.grid(row=4, column=0, columnspan = 2, sticky="nsw")
        self.imSizeSummary.grid(row=5, column=0, columnspan = 2, sticky="nsew")

class TabProtusionSummary(tk.Frame):
    """
    Class that shows cell shape parameters in a treeview widget.
    """

    def __init__(self, data, master, controller):
        """
        Initialize the summary table to show
        """

        tk.Frame.__init__(self, master)

        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Customize a treeview
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 11))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders

        # Create the widget
        self.tree = ttk.Treeview(self, style="mystyle.Treeview")

        # Definition of the columns
        self.tree["columns"] = ("one", "two", "three")
        self.tree.column("#0", width=100)
        self.tree.column("one", width=200)
        self.tree.column("two", width=150)
        self.tree.column("three", width=250)

        unit = controller.img.imgfile.unit # metadata info, physical size unit (see imagemanager module)

        if unit is None:
            unit = 'pixel'

        # Definition of the headings
        self.tree.heading("#0", text="Name", anchor=tk.W)
        self.tree.heading("one", text=('Cell Area' + ' [' + unit + '\u00B2]'), anchor=tk.W)
        # \u00B2 is the unicode super character for number 2
        self.tree.heading("two", text="# Prim Prot.", anchor=tk.W)
        self.tree.heading("three", text = ('Prim Prot Lengths' + ' [' + unit + ']'), anchor=tk.W)

        self.protTab = protusion_tab(data)

        stringValue = self.protTab.loc[:, self.protTab.columns != 'euclidean-length'].to_string(header=False,
                                                                                                index=False,
                                                                                                index_names=False).split('\n')
        values = [ele.strip(' ').split() for ele in stringValue]
        protlengthString = self.protTab.loc[:, self.protTab.columns == 'euclidean-length'].to_string(header=False,
                                                                                                     index=False,
                                                                                                     index_names=False).split('\n')
        try:
            for i in range(len(values)):
                values[i].append(protlengthString[i].strip(' '))
                self.tree.insert('', 'end', text= ('Cell # ' + values[i][0]), values = values[i][1:])
        except IndexError:
            self.tree.insert('', 'end', text = '', values=('', '', ''))

        self.tree.grid(row=0, column=0, sticky="nswe")


class TabConnectionSummary(tk.Frame):
    """
    Class that shows cell shape parameters in a treeview widget.
    """

    def __init__(self, data, master, controller):
        """
        Initialize the summary table to show
        """

        tk.Frame.__init__(self, master)

        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Customize a treeview
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 11))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders

        # Create the widget
        self.tree = ttk.Treeview(self, style="mystyle.Treeview")

        # Definition of the columns
        self.tree["columns"] = ("one", "two", "three","four")
        self.tree.column("#0", width=100)
        self.tree.column("one", width=200)
        self.tree.column("two", width=200)
        self.tree.column("three", width=200)
        self.tree.column("four", width=200)

        # Definition of the headings
        self.tree.heading("#0", text='Z Frame', anchor=tk.W)
        self.tree.heading("one", text = '# Cell 1', anchor=tk.W)
        self.tree.heading("two", text = '# Cell 2', anchor=tk.W)
        self.tree.heading("three", text = 'Center X', anchor=tk.W)
        self.tree.heading("four", text = 'Center Y', anchor=tk.W)

        x = data.loc[:, data.columns != 'zframe'].to_string(header=False, index=False, index_names=False).split('\n')
        values = [ele.strip(' ').split() for ele in x]
        try:
            for i in range(len(values)):
                self.tree.insert('', 'end', text= str(data.zframe.tolist()[i]+1), values = values[i])
        except IndexError:
            self.tree.insert('', 'end', text = '', values=('', '', '', ''))
        except AttributeError:
            self.tree.insert('', 'end', text = '', values=('', '', '', ''))

        self.tree.grid(row=0, column=0, sticky="nswe")


class TabImageSizeSummary(tk.Frame):
    """
    Class that shows image size parameters in a treeview widget.
    """

    def __init__(self, imgfile, master, controller):
        """
        Initialize the summary table to show
        """

        tk.Frame.__init__(self, master)

        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Customize a treeview
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 11))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders

        # Create the widget
        self.tree = ttk.Treeview(self, style="mystyle.Treeview")

        # you can suppress the column identifier (#0) that by setting the show parameter
        self.tree['show'] = 'headings'

        # Definition of the columns
        self.tree["columns"] = ("one", "two", "three", "four", "five")
        self.tree.column("one", width=120)
        self.tree.column("two", width=160)
        self.tree.column("three", width=150)
        self.tree.column("four", width=250)
        self.tree.column("five", width=250)

        unit = imgfile.unit  # metadata info, physical size unit (see imagemanager module)

        if unit is None:
            unit = 'pixel'

        # Definition of the headings
        self.tree.heading("one", text='Timepoints', anchor=tk.W)
        self.tree.heading("two", text='Image Size', anchor=tk.W)
        self.tree.heading("three", text='Z-stack Frames', anchor=tk.W)
        self.tree.heading("four", text='Pixels Physical Size' + ' [' + unit + ']', anchor=tk.W)
        self.tree.heading("five", text='Imaged Volume Size' + ' [' + unit + ']', anchor=tk.W)

        # from imagemanager module
        values = [str(imgfile.imgcount),
                  '{} x {}'.format(*(imgfile.imgsize['x'], imgfile.imgsize['y'])),
                  str(imgfile.shape[2])]
        try:
            l = [str(round(i,2)) for i in imgfile.dxyz]
            values.append(' x '.join(l))
            l = [str(round(i,1)) for i in imgfile.volxyz]
            values.append(' x '.join(l))
        except AttributeError:
            values.append('-')
            values.append('-')

        self.tree.insert('', 'end', values=values)

        self.tree.grid(row=0, column=0, sticky="nswe")







