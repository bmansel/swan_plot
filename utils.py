'''
This is it

'''

import sys 
#sys.path.insert(0, "/opt/dectris/albula/4.1/bin") 
#sys.path.insert(0, "/opt/dectris/albula/4.1/python") 
#import dectris.albula
import numpy as np
import fabio
import os
import tifffile
import pyFAI
#import imutils
#import cv2
import PIL.Image as IImage

from pyFAI import azimuthalIntegrator
#from PyQt5 import QtCore, QtGui, QtWidgets
#from dataclasses import dataclass
#from matplotlib import pyplot
from pathlib import Path

from scipy import ndimage as ndi 
from skimage.morphology import disk
from skimage import io


# adding below for matplotlib
#from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QVBoxLayout, QInputDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from matplotlib.transforms import IdentityTransform, TransformedBbox, Bbox

from matplotlib.colors import SymLogNorm
import random

# def combine_masks(eiger_mask, user_mask, reject_mask):
#     combined_mask = eiger_mask + user_mask + reject_mask
#     combined_mask[combined_mask > 1] = 1
#     #combined_mask[combined_mask > 1] = 1
#     return np.array(combined_mask)

def make_saturated_mask(frame, bit_depth):
    # mask vales are 2^bit_depth-1 
    maskPixels = np.squeeze(np.where(frame == 2**bit_depth - 1))
    print(np.sum(maskPixels))
    #print(np.sum(maskPixels))
    frame.fill(0)
    # for pyFAI masked values are 1 and rest are 0
    frame[maskPixels[0], maskPixels[1]] = 1
    return np.array(frame)

def combine_masks(mask,*args):
    for item in args:
        mask += item
    
    mask[mask > 1] = 1
    return mask

def make_reject_mask(image, reject_data):
    # take x, y reject data and make 2d image mask
    # image[image == 1] = 0  # this is zero already
    image[np.array(reject_data[:, 1], dtype=np.int_),
          np.array(reject_data[:, 0], dtype=np.int_)] = 1
    return np.array(image)

def append_name(key,dic):
    counter = 0
    if key in dic:
        suff = key.split("_")[-1]
        
        if suff.isnumeric():
            counter = int(suff)
            pref = key.split("_")[:-1]
            pref = '_'.join(map(str,pref))
        else: 
            counter = 0
            pref = key

        while True:
            counter += 1
            newkey = pref + '_' + str(counter)
            if newkey in dic:
                continue
            else:
                key = newkey
                break
    return key

def readSAXSpar(fname):
        def makeFIT2dDic():
            FIT2dParams = {'directBeam': None, 'energy': None, 'beamX': None,
                   'beamY': None, 'tilt': None, 'tiltPlanRotation': None, 'detector': None}
            return FIT2dParams
        
        FIT2dParams = makeFIT2dDic()
        FIT2dParams['detector'] = "eiger9m"
        FIT2dParams['tiltPlanRotation'] = 0.0
        FIT2dParams['tilt'] = 0.0
        lines = []
        count = 0
        with open(os.path.join(fname), encoding="utf8", errors='ignore') as f:
            lines = f.readlines()

        for count, line in enumerate(lines):
            if count == 3:
                FIT2dParams['energy'] = float(line.split()[0])
            if count == 8:
                FIT2dParams['beamX'] = float(line.split()[0])
                # 9m is in correct orientation both on same line
                FIT2dParams['beamY'] = float(line.split()[1])
            if count == 9:
                FIT2dParams['directBeam'] = float(line.split()[0])
        return FIT2dParams

def readHeaderFile(direc, fname):
    #global rigi, civi, expTime
        lines = []
        with open(os.path.join(direc, fname + "002.txt")) as f:
            lines = f.readlines()

        numLines = 0
        for line in lines:
            numLines += 1
        numFrames = numLines / 7

        # get civi, rigi and exposure time values
        civi = []
        rigi = []
        expTime = []
        count = 0
        for line in lines:
            count += 1
            if count > numFrames and count <= 2*numFrames:
                civi.append(float(f'{line}'))
            if count > 2*numFrames and count <= 3*numFrames:
                rigi.append(float(f'{line}'))
            if count > 4*numFrames and count <= 5*numFrames:
                expTime.append(float(f'{line}'))
        f.close()
        return civi, rigi, expTime

def rotate_about_point(xy, deg, origin):
        rads = np.deg2rad(deg)
        x, y = xy
        ox, oy = origin

        qx = ox + np.cos(rads) * (x - ox) + np.sin(rads) * (y - oy)
        qy = oy + -np.sin(rads) * (x - ox) + np.cos(rads) * (y - oy)

        #offset_x, offset_y = origin
        #adjusted_x = (x - offset_x)
        #adjusted_y = (y - offset_y)
        #cos_rad = np.cos(rads)
        #sin_rad = np.sin(rads)
        #qx = offset_x + cos_rad * adjusted_x + sin_rad * adjusted_y
        #qy = offset_y + -sin_rad * adjusted_x + cos_rad * adjusted_y

        return (qx,qy)     

def calc_new_corners(lenX, lenY, cX, cY, ang):
        
    corner_pos = {
        "LL" : (0,0),
        "UL" : (0,lenY),
        "LR" : (lenX,0),
        "UR" : (lenX,lenY)
    }
    
    new_corner_pos = {}
    
    for pos in corner_pos:
        new_corner_pos[pos] = rotate_about_point(corner_pos[pos], ang, (cX, cY))

    return new_corner_pos

def calc_shifted_corners(self, padLx, padDy, oLx, oLy, cX, cY):
    
    
    corner_pos = {
        "LL" : (padLx, padDy),
        "UL" : (padLx,oLy+padDy),
        "LR" : (oLx + padLx,padDy),
        "UR" : (oLx + padLx,oLy + padDy)
    }

    deg = self.dsb_rot_ang.value()
    
    new_corner_pos = {}
    
    for pos in corner_pos:
        new_corner_pos[pos] = self.rotate_about_point(corner_pos[pos], deg, (cX + padLx, cY + padDy))

    return new_corner_pos


def calc_pad_size(new_corner_pos, Lx, Ly ):
    
    newX = []
    newY = []
    for pos in new_corner_pos:
        x, y = new_corner_pos[pos]
        newX.append(x)
        newY.append(y)
    print(newX)
    print(newY)

    padLx = np.ceil(np.min(newX) - 0)
    padRx = np.ceil(np.max(newX)- Lx)

    padDy = np.ceil(np.min(newY) - 0)
    padUy = np.ceil(np.max(newY) - Ly)

    print("min X pad " + str( padLx ))
    print("max X Pad " + str( padRx ))
    print("min Y pad " + str( padDy ))
    print("max Y pad " + str( padUy ))
    
    if padLx < 0:
        padLx = int(np.abs(padLx))
    else:
        padLx = int(0)

    if padRx < 0:
        padRx = int(0)
    else:
        padRx = int(padRx)


    if padDy < 0:
        padDy = int(np.abs(padDy))
    else:
        padDy = int(padDy)
    
    if padUy < 0:
        padUy = int(0)
    else:
        padUy = int(padUy)

    
    return padLx, padRx, padDy, padUy

class AngleAnnotation(Arc):
    """
    Draws an arc between two vectors which appears circular in display space.
    """
    def __init__(self, xy, p1, p2, size=75, unit="points", ax=None,
                 text="", textposition="inside", text_kw=None, **kwargs):
        """
        Parameters
        ----------
        xy, p1, p2 : tuple or array of two floats
            Center position and two points. Angle annotation is drawn between
            the two vectors connecting *p1* and *p2* with *xy*, respectively.
            Units are data coordinates.

        size : float
            Diameter of the angle annotation in units specified by *unit*.

        unit : str
            One of the following strings to specify the unit of *size*:

            * "pixels": pixels
            * "points": points, use points instead of pixels to not have a
              dependence on the DPI
            * "axes width", "axes height": relative units of Axes width, height
            * "axes min", "axes max": minimum or maximum of relative Axes
              width, height

        ax : `matplotlib.axes.Axes`
            The Axes to add the angle annotation to.

        text : str
            The text to mark the angle with.

        textposition : {"inside", "outside", "edge"}
            Whether to show the text in- or outside the arc. "edge" can be used
            for custom positions anchored at the arc's edge.

        text_kw : dict
            Dictionary of arguments passed to the Annotation.

        **kwargs
            Further parameters are passed to `matplotlib.patches.Arc`. Use this
            to specify, color, linewidth etc. of the arc.

        """
        self.ax = ax or plt.gca()
        self._xydata = xy  # in data coordinates
        self.vec1 = p1
        self.vec2 = p2
        self.size = size
        self.unit = unit
        self.textposition = textposition

        super().__init__(self._xydata, size, size, angle=0.0,
                         theta1=self.theta1, theta2=self.theta2, **kwargs)

        self.set_transform(IdentityTransform())
        self.ax.add_patch(self)

        self.kw = dict(ha="center", va="center",
                       xycoords=IdentityTransform(),
                       xytext=(0, 0), textcoords="offset points",
                       annotation_clip=True)
        self.kw.update(text_kw or {})
        self.text = ax.annotate(text, xy=self._center, **self.kw)

    def get_size(self):
        factor = 1.
        if self.unit == "points":
            factor = self.ax.figure.dpi / 72.
        elif self.unit[:4] == "axes":
            b = TransformedBbox(Bbox.unit(), self.ax.transAxes)
            dic = {"max": max(b.width, b.height),
                   "min": min(b.width, b.height),
                   "width": b.width, "height": b.height}
            factor = dic[self.unit[5:]]
        return self.size * factor

    def set_size(self, size):
        self.size = size

    def get_center_in_pixels(self):
        """return center in pixels"""
        return self.ax.transData.transform(self._xydata)

    def set_center(self, xy):
        """set center in data coordinates"""
        self._xydata = xy

    def get_theta(self, vec):
        vec_in_pixels = self.ax.transData.transform(vec) - self._center
        return np.rad2deg(np.arctan2(vec_in_pixels[1], vec_in_pixels[0]))

    def get_theta1(self):
        return self.get_theta(self.vec1)

    def get_theta2(self):
        return self.get_theta(self.vec2)

    def set_theta(self, angle):
        pass

    # Redefine attributes of the Arc to always give values in pixel space
    _center = property(get_center_in_pixels, set_center)
    theta1 = property(get_theta1, set_theta)
    theta2 = property(get_theta2, set_theta)
    width = property(get_size, set_size)
    height = property(get_size, set_size)

    # The following two methods are needed to update the text position.
    def draw(self, renderer):
        self.update_text()
        super().draw(renderer)

    def update_text(self):
        c = self._center
        s = self.get_size()
        angle_span = (self.theta2 - self.theta1) % 360
        angle = np.deg2rad(self.theta1 + angle_span / 2)
        r = s / 2
        if self.textposition == "inside":
            r = s / np.interp(angle_span, [60, 90, 135, 180],
                                          [3.3, 3.5, 3.8, 4])
        self.text.xy = c + r * np.array([np.cos(angle), np.sin(angle)])
        if self.textposition == "outside":
            def R90(a, r, w, h):
                if a < np.arctan(h/2/(r+w/2)):
                    return np.sqrt((r+w/2)**2 + (np.tan(a)*(r+w/2))**2)
                else:
                    c = np.sqrt((w/2)**2+(h/2)**2)
                    T = np.arcsin(c * np.cos(np.pi/2 - a + np.arcsin(h/2/c))/r)
                    xy = r * np.array([np.cos(a + T), np.sin(a + T)])
                    xy += np.array([w/2, h/2])
                    return np.sqrt(np.sum(xy**2))

            def R(a, r, w, h):
                aa = (a % (np.pi/4))*((a % (np.pi/2)) <= np.pi/4) + \
                     (np.pi/4 - (a % (np.pi/4)))*((a % (np.pi/2)) >= np.pi/4)
                return R90(aa, r, *[w, h][::int(np.sign(np.cos(2*a)))])

            bbox = self.text.get_window_extent()
            X = R(angle, r, bbox.width, bbox.height)
            trans = self.ax.figure.dpi_scale_trans.inverted()
            offs = trans.transform(((X-s/2), 0))[0] * 72
            self.text.set_position([offs*np.cos(angle), offs*np.sin(angle)])

class Data_2d_rot:
    '''GUI/

    '''
    def __init__(self,direc, ext, name, array, info):
            self.direc = direc
            self.ext = ext
            self.name = name
            self.array = array
            self.info = info



class Data_2d:
    '''GUI/

    '''
    def __init__(self,direc, ext, name, array, info):
            self.dir = direc
            self.ext = ext
            self.name = name
            self.array = array
            self.info = info

    def integrate_2D(self,ai,mask):
        return ai.integrate2d(
            self.array,
            500,
            360,
            filename=None, 
            correctSolidAngle=True,
            variance=None,
            error_model=None,
            radial_range=None,
            azimuth_range=None,
            mask=mask,
            dummy=None,
            delta_dummy=None,
            polarization_factor=None,
            dark=None,
            flat=None,
            method='cython',
            unit='q_A^-1',
            safe=False,
            metadata=None
        )
        
    
    def remove_outliers(self, radius, threshold):
        footprint_function = disk
        footprint = footprint_function(radius=radius)
        median_filtered = ndi.median_filter(self.array, footprint=footprint)
        # Bright  and dark:
        #outliers = (image > median_filtered + threshold) | (image < median_filtered - threshold)
        # bright only
        outliers = (self.array > median_filtered + threshold)
        
        output = np.where(outliers,median_filtered,self.array)
        return output

    def rotate(self, deg):
        
        image = IImage.fromarray(self.array) 
        new_img = image.rotate(deg, expand=True) 

        return np.asarray(new_img)

    def pad_rotate_image(self,data):
        
        #cX = float(self.lineEdit_X_dir.text().strip())
        #cY = float(self.lineEdit_Y_dir.text().strip())

        Ly, Lx = data.data.shape
        
        # calculate where corners are after first rotation
            
        #new_corner_pos = self.calc_new_corners(Lx, Ly, cX, cY)
        
        # calculate new padding size
        #padLx, padRx, padDy, padUy = self.calc_pad_size(new_corner_pos, Lx, Ly)
        # calculate new center
        #cX += padLx
        #cY += padDy
        
        #for val in range(1):    
            # calculate where the original points are after the rotation
            # shifted_corners = self.calc_shifted_corners(padLx, padDy, Lx, Ly, cX, cY)
            # nLx = Lx + padLx + padRx
            # nLy = Ly + padDy + padUy
            # calculate new padding size
            #newPadLx, newPadRx, newPadDy, newPadUy = self.calc_pad_size(shifted_corners, nLx, nLy)
            
            # padLx += newPadLx
            # padRx += newPadRx 
            # padDy += newPadDy
            # padUy += newPadUy
            # calculate new center
            #cX += padLx
            #cY += padDy  

            # print(val)
            # print(padLx)
            # print(padRx)
            # print(padDy)
            # print(padUy)

        cX = float(self.lineEdit_X_dir.text().strip())
        cY = float(self.lineEdit_Y_dir.text().strip())

        # Use symmetrical padding with the longest side:
        if Ly > Lx:
            padL = Ly
        elif Lx > Ly:
            padL = Lx
        else:
            padL = Lx

        shifted_corners = self.calc_shifted_corners(padL, padL, Lx, Ly, cX, cY)
        newX = []
        newY = []
        for pos in shifted_corners:
            x, y =shifted_corners[pos]
            newX.append(x)
            newY.append(y)
        print("min X index is: ", np.round(np.min(newX)))
        print("max X index is: ", np.round(np.max(newX)))
        print("min Y index is: ", np.round(np.min(newY)))
        print("max Y index is: ", np.round(np.max(newY)))

        minX = np.round(np.min(newX))
        maxX = np.round(np.max(newX))
        minY = np.round(np.min(newY))
        maxY = np.round(np.max(newY))
        
        
        
        deg = self.dsb_rot_ang.value()
        #pad_img = np.pad(data.data, ((padL,padL),(padL, padL)),'constant', constant_values=(0,0))    
        #pad_img = np.pad(data.data, ((padDy,padUy),(padRx, padLx)),'constant', constant_values=(0,0))
        
        test_image = IImage.fromarray(data.data) # pad_img
        
        new_img = test_image.rotate(deg, expand=True) #, center=(cX+padL, cY+padL), resample=IImage.Resampling.BICUBIC)

        rot_img = np.asarray(new_img)
        #rot_img = rot_img[int(minY):int(maxY),int(minX):int(maxX)]

        return rot_img
    
    
    def integrate_image(self, ai, q_bins, chi_start,chi_end, mask, normValue):

        q, I, err = ai.integrate1d(
            self.array,
             q_bins,
            correctSolidAngle=True,
            variance=None,
            error_model="poisson",
            radial_range=None, 
            azimuth_range=(chi_start,chi_end), 
            mask=mask,
            dummy=None, 
            delta_dummy=None, 
            polarization_factor=None, 
            dark=None, 
            flat=None, 
            method='cython', 
            unit='q_A^-1', 
            safe=False, 
            normalization_factor=normValue, 
            metadata=None)
        return q, I, err


class Data_2d_az:
    def __init__(self,direc,ext,name,array,info) -> None:
        self.direc = direc
        self.ext = ext
        self.name = name
        self.array = array
        self.info = info

class Data_1d_az:
    '''
    Some stuff


    '''
    def __init__(self,direc,ext,name,chi,I,info) -> None:
        self.dir = direc
        self.ext = ext
        self.name = name
        self.chi = chi
        self.I = I
        self.info = info

class Data_1d:
    '''
    Some stuff


    '''
    def __init__(self,direc,ext,name,q,I,err,info) -> None:
        self.dir = direc
        self.ext = ext
        self.name = name
        self.q = q
        self.I = I
        self.err = err
        self.info = info
