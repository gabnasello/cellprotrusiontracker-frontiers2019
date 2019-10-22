"""
Created on Fri Oct 31st 2018

Module to process microscope images in a GUI.

@author: Gabriele Nasello
"""

from skimage.morphology import medial_axis
import numpy as np
from skimage.measure import regionprops
from skimage import filters
from scipy.ndimage.measurements import label
from copy import deepcopy
from skimage.graph import route_through_array
from skan import csr
from scipy import ndimage


def path_length(pixel_path, skel_image, physicspacing):
    "Measure the euclidian length of a pixel path (e.g. skeleton branch)"
    prot = np.zeros(skel_image.shape)
    prot[pixel_path[:, 0], pixel_path[:, 1]] = 1

    length = csr.summarise(prot, spacing = physicspacing)['euclidean-distance'][0]
    return length

def automatic_cellbody_threshold(distmap):
    """The automatic algorithm to extract cell body skeleton assumes that pixels of the medial axis
    transform of the cell body have higher distance to the mask boundary.
    Thus, it's possible to isolate those pixels of the medial axis transform by applying a
    thresholding technique (Otsu) to the intensity histogram.

    distmap : distance map of the whole cell skeleton
    """

    # List of non-zero elements from distOnSkel
    distNzero = distmap[np.nonzero(distmap)]

    # Isolate cell body from histogram pixel intensity of the medial axis transform, by applying the Otsu method.
    threshold = filters.threshold_otsu(distNzero)
    maxthreshold = distNzero.max()

    return threshold, maxthreshold

def cellbody_skeletonization(distmap, threshold, maxthre, physicspacing):
    """
    Function to extract the cell body skeleton after madial axis transform thresholding.
    :param distmap:
    :param threshold:
    :return:
    """
    skelCellBody = {'skeleton': [],
                    'endpointCoord': [],
                    'paths': [],
                    'legnths': [],
                    'physical-space': physicspacing,
                    'threshold': threshold,
                    'maxthreshold': maxthre}

    BodyThreshInd = distmap < threshold
    distCellBody = deepcopy(distmap)
    distCellBody[BodyThreshInd] = 0

    # if more separate regions are selected, choose the longest one as cell body skeleton by label each separated region
    # and disacrding the shortest ones.
    structure = np.ones((3, 3), dtype=np.int)  # in this case we allow any kind of connection
    labeled, ncomponents = label(distCellBody, structure)
    regprop = regionprops(labeled)

    len_region = [i.perimeter for i in regprop]
    skelCellBody['skeleton'] = labeled == (np.argmax(len_region) + 1)

    # cell body edge detection
    skelCellBody['endpointCoord'] = edgepoint_detect(skelCellBody['skeleton'])

    pathCellBody = []
    cellBodyLengths = []
    for coord in skelCellBody['endpointCoord'][1:]:
        Path, _ = route_through_array(skelCellBody['skeleton'] == 0, start=skelCellBody['endpointCoord'][0], end=coord)
        Path = np.array(Path)
        pathCellBody.append(Path)
        Length = path_length(Path, skelCellBody['skeleton'], physicspacing)
        cellBodyLengths.append(Length)

    skelCellBody['paths'] = pathCellBody
    skelCellBody['lengths'] = cellBodyLengths

    return skelCellBody

def edgepoint_detect(skeleton_image):
    " Function to detect end points of the skeleton by the application of the hit-and-miss operation"

    endpoint1 = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 1]])
    endpoint2 = np.array([[0, 0, 0], [0, 1, 0], [0, 1, 0]])
    endpoint3 = np.array([[0, 0, 0], [0, 1, 0], [1, 0, 0]])
    endpoint4 = np.array([[0, 0, 0], [1, 1, 0], [0, 0, 0]])
    endpoint5 = np.array([[0, 0, 0], [0, 1, 1], [0, 0, 0]])
    endpoint6 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 0]])
    endpoint7 = np.array([[0, 1, 0], [0, 1, 0], [0, 0, 0]])
    endpoint8 = np.array([[0, 0, 1], [0, 1, 0], [0, 0, 0]])

    ep1 = ndimage.binary_hit_or_miss(skeleton_image, endpoint1)
    ep2 = ndimage.binary_hit_or_miss(skeleton_image, endpoint2)
    ep3 = ndimage.binary_hit_or_miss(skeleton_image, endpoint3)
    ep4 = ndimage.binary_hit_or_miss(skeleton_image, endpoint4)
    ep5 = ndimage.binary_hit_or_miss(skeleton_image, endpoint5)
    ep6 = ndimage.binary_hit_or_miss(skeleton_image, endpoint6)
    ep7 = ndimage.binary_hit_or_miss(skeleton_image, endpoint7)
    ep8 = ndimage.binary_hit_or_miss(skeleton_image, endpoint8)

    endpoint = ep1 + ep2 + ep3 + ep4 + ep5 + ep6 + ep7 + ep8

    # endpoint pixel coordinates
    coord = np.argwhere(endpoint)

    return coord


def sum_neighbour_pixels(pixel, image):
    """
    Function to sum the intensity values of the 8 neighbours of a specific 2D pixel.
    :param pixel:
    :param image:
    :return:
    """
    r = pixel[0]
    c = pixel[1]

    neighbours = []
    neighbours.append(image[r - 1, c - 1])
    neighbours.append(image[r - 1, c])
    neighbours.append(image[r - 1, c + 1])
    neighbours.append(image[r, c - 1])
    neighbours.append(image[r, c + 1])
    neighbours.append(image[r + 1, c + 1])
    neighbours.append(image[r + 1, c])
    neighbours.append(image[r + 1, c - 1])

    return sum(neighbours)

def branch_parameters_extration(distmap, skelbranch, physicspacing):
    """
    Extract branches data from skeleton such as primary branche lengths, paths, initial and final pixels.
    :param skelBranches:
    :param physicspacing:
    :return:
    """

    skeldict = {'protusion_id': [],
                'initial_node-id': [],
                'initial_node-coord-0': [],
                'initial_node-coord-1': [],
                'final_node-id': [],
                'final_node-coord-0': [],
                'final_node-coord-1': [],
                'euclidean-length': [],
                'primary-path': [],
                'secondary-paths': [],
                'total-protlength': [],
                'physical-space': physicspacing,
                 }

    # Intermediate objects to measure the length of skeleton branches, see the skan module
    _, c0, _ = csr.skeleton_to_csgraph(skelbranch)
    # c0 : An array of shape (Nnz + 1, skel.ndim), mapping indices in graph to pixel coordinates
    # in degree_image or skel.

    branch_data = csr.summarise(skelbranch, spacing=physicspacing)
    # total protusion length
    totprotlength = branch_data['euclidean-distance'].sum()
    skeldict['total-protlength'] = totprotlength

    skeletonEdges = edgepoint_detect(distmap > 0)
    branchEdges = edgepoint_detect(skelbranch)

    removeInd = np.where((branchEdges == skeletonEdges[:, None]).all(-1))[1]
    endbodycoord = np.delete(branchEdges, removeInd, 0)

    skeldict['initial_node-coord-0'] = endbodycoord[:, 0].tolist()
    skeldict['initial_node-coord-1'] = endbodycoord[:, 1].tolist()

    # Matrix that relates nodeid in the branch_data dataframe and pixel coordinates
    nodeIDallPixels = c0.astype(int)

    # Node id of endpoints, , by using NumPy broadcasting
    nodeIDendBody = np.where((nodeIDallPixels == endbodycoord[:, None]).all(-1))[1]
    skeldict['initial_node-id'] = nodeIDendBody.tolist()

    # label separate branches starting from the cell body
    structure = np.ones((3, 3), dtype=np.int)  # in this case we allow any kind of connection
    labeled, ncomponents = label(skelbranch, structure)

    labelValue = labeled[endbodycoord[:, 0], endbodycoord[:, 1]]
    skeldict['protusion_id'] = labelValue.tolist()
    skeldict['protusion_id'] = np.arange(ncomponents) + 1

    for i in range(ncomponents):

        # skeleton of single protusion
        skelProt = labeled == labelValue[i]

        # protusion edges in black background
        endprotCoord = edgepoint_detect(skelProt)
        # # remove cellbody endpoint from protusion endpoint list
        # endpointProt[endbodycoord[i - 1, 0], endbodycoord[i - 1, 1]] = 0
        removeInd = np.where((endprotCoord == endbodycoord[:, None]).all(-1))[1]
        endprotCoord = np.delete(endprotCoord, removeInd, 0)

        # node id of protusion endpoints, by using NumPy broadcasting
        endprotNodeID = np.where((nodeIDallPixels == endprotCoord[:, None]).all(-1))[1]

        protPaths = []
        protLengths = []
        for coord in endprotCoord:
            Path, _ = route_through_array(np.invert(skelProt), start=endbodycoord[i], end=coord)
            Path = np.array(Path)
            protPaths.append(Path)
            Length = path_length(Path, skelProt, physicspacing)
            protLengths.append(Length)


        maxLength = np.array(protLengths).max()
        skeldict['euclidean-length'].append(maxLength)

        primaryPathID = np.array(protLengths).argmax()
        primaryPath = protPaths[primaryPathID]
        skeldict['primary-path'].append(primaryPath)

        # get only secondary paths
        del (protPaths[primaryPathID])
        skeldict['secondary-paths'].append(protPaths)

        skeldict['final_node-id'].append(endprotNodeID[primaryPathID])
        skeldict['final_node-coord-0'].append(endprotCoord[primaryPathID, 0])
        skeldict['final_node-coord-1'].append(endprotCoord[primaryPathID, 1])

    return skeldict

def branch_skletonization(distmap, bodydict, physicspacing):
    """
    Function to sum the intensity values of the 8 neighbours of a specific 2D pixel.
    :param pixel:
    :param image:
    :return:
    """
    # skeleton cell brunches
    # skelBranches = deepcopy(distOnSkel)
    skeletonBody = bodydict['skeleton']
    endBodyCoord = bodydict['endpointCoord']
    skelbranch = deepcopy(distmap)
    skelbranch[skeletonBody] = 0
    skelbranch[skelbranch > 0] = 1
    skelbranch = skelbranch.astype(int)

    protdict = branch_parameters_extration(distmap, skelbranch, physicspacing)

    return protdict

def full_cell_skeletonization(distmap, threshold, maxthreshold, physicspacing = 1):
    """
    Execute a complete skeletonization analysis starting from a threshold value
    used to separate cell body skeleton from branches.
    :param distmap:
    :param threshold:
    :param physicspacing:
    :return:
    """
    # full cell body skeletonization and analysis
    bodydict = cellbody_skeletonization(distmap, threshold, maxthreshold, physicspacing)

    # full cell branches skeletonization and analysis
    protdusiondict = branch_skletonization(distmap, bodydict, physicspacing)

    return bodydict, protdusiondict

class SkelProc():

    """
    Class that contains all the methods necessary to process a cell mask and extract skeleton parameters in a GUI.
    """

    def __init__(self, parent, controller):
        """
        Initialize the object
        """

        self.controller = controller
        self.parent = parent

        self.mask = []

    def skletonize_cell(self, cellmask):
        """
        Skeletonize cell mask image, applying an automatic algorithm to identify cell body.
        """
        self.mask = cellmask
        controller = self.controller

        # Compute the medial axis (skeleton) and the distance transform
        medialAxis, distance = medial_axis(cellmask, return_distance=True)

        if controller.img.imgfile.dxyz is not None:
            physpace = controller.img.imgfile.dxyz[0]

        # Distance to the background for pixels of the skeleton
        distmap = np.array(distance * medialAxis)

        self.thresh, maxthreshold = automatic_cellbody_threshold(distmap)

        self.skelbody, self.skelprot = full_cell_skeletonization(distmap, self.thresh, maxthreshold, physpace)





