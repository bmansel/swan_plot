"""
This is it

"""
import cv2
import numpy as np
import os
import fabio
import PIL.Image as IImage
import matplotlib.pyplot as plt
import time
from pathlib import Path
from matplotlib.patches import Arc
from matplotlib.transforms import IdentityTransform, TransformedBbox, Bbox
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import tifffile


def make_saturated_mask(frame, bit_depth):
    # mask vales are 2^bit_depth-1
    maskPixels = np.squeeze(np.where(frame == 2**bit_depth - 1))
    frame.fill(0)
    # for pyFAI masked values are 1 and rest are 0
    frame[maskPixels[0], maskPixels[1]] = 1
    return np.array(frame)


def combine_masks(mask, *args):
    for item in args:
        mask += item

    mask[mask > 1] = 1
    return mask


def make_reject_mask(image, reject_data):
    # take x, y reject data and make 2d image mask
    # image[image == 1] = 0  # this is zero already
    image[
        np.array(reject_data[:, 1], dtype=np.int_),
        np.array(reject_data[:, 0], dtype=np.int_),
    ] = 1
    return np.array(image)


def append_name(key, dic):
    counter = 0
    if key in dic:
        suff = key.split("_")[-1]

        if suff.isnumeric():
            counter = int(suff)
            pref = key.split("_")[:-1]
            pref = "_".join(map(str, pref))
        else:
            counter = 0
            pref = key

        while True:
            counter += 1
            newkey = pref + "_" + str(counter)
            if newkey in dic:
                continue
            else:
                key = newkey
                break
    return key


def readSAXSpar(fname):
    def makefit2d_dic():
        FIT2dParams = {
            "directBeam": None,
            "energy": None,
            "beamX": None,
            "beamY": None,
            "tilt": None,
            "tiltPlanRotation": None,
            "detector": None,
        }
        return FIT2dParams

    FIT2dParams = makefit2d_dic()
    FIT2dParams["detector"] = "eiger9m"
    FIT2dParams["tiltPlanRotation"] = 0.0
    FIT2dParams["tilt"] = 0.0
    lines = []
    count = 0
    with open(os.path.join(fname), encoding="utf8", errors="ignore") as f:
        lines = f.readlines()

    for count, line in enumerate(lines):
        if count == 3:
            FIT2dParams["energy"] = float(line.split()[0])
        if count == 8:
            FIT2dParams["beamX"] = float(line.split()[0])
            # 9m is in correct orientation both on same line
            FIT2dParams["beamY"] = float(line.split()[1])
        if count == 9:
            FIT2dParams["directBeam"] = float(line.split()[0])
    return FIT2dParams


def readHeaderFile(direc, fname):
    # global rigi, civi, expTime
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
        if count > numFrames and count <= 2 * numFrames:
            civi.append(float(f"{line}"))
        if count > 2 * numFrames and count <= 3 * numFrames:
            rigi.append(float(f"{line}"))
        if count > 4 * numFrames and count <= 5 * numFrames:
            expTime.append(float(f"{line}"))
    f.close()
    return civi, rigi, expTime


def rotate_about_point(xy, deg, origin):
    rads = np.deg2rad(deg)
    x, y = xy
    ox, oy = origin

    qx = ox + np.cos(rads) * (x - ox) + np.sin(rads) * (y - oy)
    qy = oy + -np.sin(rads) * (x - ox) + np.cos(rads) * (y - oy)

    # offset_x, offset_y = origin
    # adjusted_x = (x - offset_x)
    # adjusted_y = (y - offset_y)
    # cos_rad = np.cos(rads)
    # sin_rad = np.sin(rads)
    # qx = offset_x + cos_rad * adjusted_x + sin_rad * adjusted_y
    # qy = offset_y + -sin_rad * adjusted_x + cos_rad * adjusted_y

    return (qx, qy)


def calc_new_corners(lenX, lenY, cX, cY, ang):
    corner_pos = {"LL": (0, 0), "UL": (0, lenY), "LR": (lenX, 0), "UR": (lenX, lenY)}

    new_corner_pos = {}

    for pos in corner_pos:
        new_corner_pos[pos] = rotate_about_point(corner_pos[pos], ang, (cX, cY))

    return new_corner_pos


def calc_shifted_corners(self, padLx, padDy, oLx, oLy, cX, cY):
    corner_pos = {
        "LL": (padLx, padDy),
        "UL": (padLx, oLy + padDy),
        "LR": (oLx + padLx, padDy),
        "UR": (oLx + padLx, oLy + padDy),
    }

    deg = self.dsb_rot_ang.value()

    new_corner_pos = {}

    for pos in corner_pos:
        new_corner_pos[pos] = self.rotate_about_point(
            corner_pos[pos], deg, (cX + padLx, cY + padDy)
        )

    return new_corner_pos


def calc_pad_size(new_corner_pos, Lx, Ly):
    newX = []
    newY = []
    for pos in new_corner_pos:
        x, y = new_corner_pos[pos]
        newX.append(x)
        newY.append(y)

    padLx = np.ceil(np.min(newX) - 0)
    padRx = np.ceil(np.max(newX) - Lx)

    padDy = np.ceil(np.min(newY) - 0)
    padUy = np.ceil(np.max(newY) - Ly)

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

    def __init__(
        self,
        xy,
        p1,
        p2,
        size=75,
        unit="points",
        ax=None,
        text="",
        textposition="inside",
        text_kw=None,
        **kwargs,
    ):
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

        super().__init__(
            self._xydata,
            size,
            size,
            angle=0.0,
            theta1=self.theta1,
            theta2=self.theta2,
            **kwargs,
        )

        self.set_transform(IdentityTransform())
        self.ax.add_patch(self)

        self.kw = dict(
            ha="center",
            va="center",
            xycoords=IdentityTransform(),
            xytext=(0, 0),
            textcoords="offset points",
            annotation_clip=True,
        )
        self.kw.update(text_kw or {})
        self.text = ax.annotate(text, xy=self._center, **self.kw)

    def get_size(self):
        factor = 1.0
        if self.unit == "points":
            factor = self.ax.figure.dpi / 72.0
        elif self.unit[:4] == "axes":
            b = TransformedBbox(Bbox.unit(), self.ax.transAxes)
            dic = {
                "max": max(b.width, b.height),
                "min": min(b.width, b.height),
                "width": b.width,
                "height": b.height,
            }
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
            r = s / np.interp(angle_span, [60, 90, 135, 180], [3.3, 3.5, 3.8, 4])
        self.text.xy = c + r * np.array([np.cos(angle), np.sin(angle)])
        if self.textposition == "outside":

            def R90(a, r, w, h):
                if a < np.arctan(h / 2 / (r + w / 2)):
                    return np.sqrt((r + w / 2) ** 2 + (np.tan(a) * (r + w / 2)) ** 2)
                else:
                    c = np.sqrt((w / 2) ** 2 + (h / 2) ** 2)
                    T = np.arcsin(c * np.cos(np.pi / 2 - a + np.arcsin(h / 2 / c)) / r)
                    xy = r * np.array([np.cos(a + T), np.sin(a + T)])
                    xy += np.array([w / 2, h / 2])
                    return np.sqrt(np.sum(xy**2))

            def R(a, r, w, h):
                aa = (a % (np.pi / 4)) * ((a % (np.pi / 2)) <= np.pi / 4) + (
                    np.pi / 4 - (a % (np.pi / 4))
                ) * ((a % (np.pi / 2)) >= np.pi / 4)
                return R90(aa, r, *[w, h][:: int(np.sign(np.cos(2 * a)))])

            bbox = self.text.get_window_extent()
            X = R(angle, r, bbox.width, bbox.height)
            trans = self.ax.figure.dpi_scale_trans.inverted()
            offs = trans.transform(((X - s / 2), 0))[0] * 72
            self.text.set_position([offs * np.cos(angle), offs * np.sin(angle)])


class Data_2d_rot:
    """GUI/"""

    def __init__(self, direc, ext, name, array, info):
        self.direc = direc
        self.ext = ext
        self.name = name
        self.array = array
        self.info = info


class Data_2d:
    """GUI/"""

    def __init__(self, direc, ext, name, array, info):
        self.dir = direc
        self.ext = ext
        self.name = name
        self.array = array
        self.info = info

    def integrate_2D(self, ai, mask):
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
            method="cython",
            unit="q_A^-1",
            safe=False,
            metadata=None,
        )

    def remove_outliers(self, radius, threshold):
        
        if self.array.dtype == 'uint32':
            median_filtered = cv2.medianBlur(self.array.astype('f'), int(radius))
            median_filtered = np.array(median_filtered, dtype='uint')
        else:
            median_filtered = cv2.medianBlur(self.array, int(radius))
        # median_filtered = ndi.median_filter(self.array, footprint=footprint)
        # Bright  and dark:
        # outliers = (image > median_filtered + threshold) | (image < median_filtered - threshold)
        # bright only
        outliers = (self.array > median_filtered + threshold) | (
            self.array < median_filtered - threshold
        )

        output = np.where(outliers, median_filtered, self.array)
        return output

    def rotate(self, deg):
        image = IImage.fromarray(self.array)
        new_img = image.rotate(deg, expand=True)

        return np.asarray(new_img)

    def pad_rotate_image(self, data):
        # cX = float(self.lineEdit_X_dir.text().strip())
        # cY = float(self.lineEdit_Y_dir.text().strip())

        Ly, Lx = data.data.shape

        # calculate where corners are after first rotation

        # new_corner_pos = self.calc_new_corners(Lx, Ly, cX, cY)

        # calculate new padding size
        # padLx, padRx, padDy, padUy = self.calc_pad_size(new_corner_pos, Lx, Ly)
        # calculate new center
        # cX += padLx
        # cY += padDy

        # for val in range(1):
        # calculate where the original points are after the rotation
        # shifted_corners = self.calc_shifted_corners(padLx, padDy, Lx, Ly, cX, cY)
        # nLx = Lx + padLx + padRx
        # nLy = Ly + padDy + padUy
        # calculate new padding size
        # newPadLx, newPadRx, newPadDy, newPadUy = self.calc_pad_size(shifted_corners, nLx, nLy)

        # padLx += newPadLx
        # padRx += newPadRx
        # padDy += newPadDy
        # padUy += newPadUy
        # calculate new center
        # cX += padLx
        # cY += padDy

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
            x, y = shifted_corners[pos]
            newX.append(x)
            newY.append(y)

        minX = np.round(np.min(newX))
        maxX = np.round(np.max(newX))
        minY = np.round(np.min(newY))
        maxY = np.round(np.max(newY))

        deg = self.dsb_rot_ang.value()
        # pad_img = np.pad(data.data, ((padL,padL),(padL, padL)),'constant', constant_values=(0,0))
        # pad_img = np.pad(data.data, ((padDy,padUy),(padRx, padLx)),'constant', constant_values=(0,0))

        test_image = IImage.fromarray(data.data)  # pad_img

        new_img = test_image.rotate(
            deg, expand=True
        )  # , center=(cX+padL, cY+padL), resample=IImage.Resampling.BICUBIC)

        rot_img = np.asarray(new_img)
        # rot_img = rot_img[int(minY):int(maxY),int(minX):int(maxX)]

        return rot_img

    def integrate_image(self, ai, q_bins, chi_start, chi_end, mask, normValue):
        q, intensity, err = ai.integrate1d(
            self.array,
            q_bins,
            correctSolidAngle=True,
            variance=None,
            error_model="poisson",
            radial_range=None,
            azimuth_range=(chi_start, chi_end),
            mask=mask,
            dummy=None,
            delta_dummy=None,
            polarization_factor=None,
            dark=None,
            flat=None,
            method=("no", "csr", "cython"),
            # method=("no", "csr", "cython"), #'cython'
            # method=("no", "histogram", "cython"),
            unit="q_A^-1",
            safe=False,
            normalization_factor=normValue,
            metadata=None,
        )
        return q, intensity, err


class Data_2d_az:
    def __init__(self, direc, ext, name, array, info) -> None:
        self.direc = direc
        self.ext = ext
        self.name = name
        self.array = array
        self.info = info


class Data_1d_az:
    """
    Some stuff


    """

    def __init__(self, direc, ext, name, chi, i, info) -> None:
        self.dir = direc
        self.ext = ext
        self.name = name
        self.chi = chi
        self.intensity = i
        self.info = info


class Data_1d:
    """
    Some stuff


    """

    def __init__(self, direc, ext, name, q, i, err, info) -> None:
        self.dir = direc
        self.ext = ext
        self.name = name
        self.q = q
        self.intensity = i
        self.err = err
        self.info = info

def remove_outliers(self,
                export_data_signal,
                cancel_signal,
                progress_signal,
                data_name,
                names_types,
                sample_data, 
                background_data, 
                subtracted_data, 
                size, 
                threshold, 
                batch_mode        
                ):
    exported = 0
    self.canceled = False

    for item in names_types:
        
        if self.canceled:
            self.deleteLater()
            return
        
        if item[1] == "smp":
            corr_data = Data_2d(
                sample_data[item[0]].dir,
                sample_data[item[0]].ext,
                "2D~" + "OLrm_" + sample_data[item[0]].name.split("~")[1],
                sample_data[item[0]].remove_outliers(size, threshold),
                sample_data[item[0]].info
            )
            #self.sample_data[corr_data.name] = corr_data
        elif item[1] == "bkg":
            corr_data = Data_2d(
                background_data[item[0]].dir,
                background_data[item[0]].ext,
                "2D~" + "OLrm_" + background_data[item[0]].name.split("~")[1],
                background_data[item[0]].remove_outliers(size, threshold),
                background_data[item[0]].info
            )
            #self.background_data[corr_data.name] = corr_data
        else:
            corr_data = Data_2d(
                subtracted_data[item[0]].dir,
                subtracted_data[item[0]].ext,
                "2D~" + "OLrm_" + subtracted_data[item[0]].name.split("~")[1],
                subtracted_data[item[0]].remove_outliers(size, threshold),
                subtracted_data[item[0]].info
            )
            #self.subtracted_data[corr_data.name] = corr_data

        export_data_signal.emit(corr_data)
        exported += 1
        if self.canceled != True:
            progress_signal.emit(int((exported / len(names_types)) * 100))
        cancel_signal.connect(self.cancel_thread)

def subtract_1d(self,
        export_data_signal,
        cancel_signal,
        progress_signal,
        data_name,
        smp_names,  
        smp_data, 
        bkg_dataset, 
        scale, 
        smp_TM, 
        bkg_TM,
        ):
    exported = 0
    self.canceled = False
    for item in smp_names:
        part1 = np.divide(smp_data[item.data()].intensity * scale, smp_TM)
        part2 = np.divide(bkg_dataset.intensity * scale, bkg_TM)
        err_p1 = np.divide(smp_data[item.data()].err * scale, smp_TM)
        err_p2 = np.divide(bkg_dataset.err * scale, bkg_TM)

        subd_data = Data_1d(
            smp_data[item.data()].dir,
            "dat",
            "1D~" + "subd_" + smp_data[item.data()].name.split("~")[1],
            smp_data[item.data()].q,
            np.subtract(part1, part2),
            np.sqrt(np.add(np.square(err_p1), np.square(err_p2))),
            {"type": "sub", "dim": "1D"}
        )
        export_data_signal.emit(subd_data)
        exported += 1
        if self.canceled != True:
            progress_signal.emit(int((exported / len(smp_names)) * 100))
        cancel_signal.connect(self.cancel_thread)
        # if self.batch_mode:
        #     self.batchmode_data.emit(corr_data)
        # else:
        #     self.data_name.emit("Processed: " + corr_data.name)

    # only plot last one
    # if not self.batch_mode:
    #     self.plot_data.emit(corr_data)



                
def integrate_data(self, 
                export_data_signal,
                cancel_signal,
                progress_signal,
                data_name,
                ai,
                sample_data,
                background_data,
                subtracted_data,
                names_types, 
                q_bins, 
                chi_start, 
                chi_end, 
                mask, 
                batch_mode,
                monitor_002
                 ):
    exported = 0
    self.canceled = False
    for item in names_types:
        if self.canceled:
            return
        TMsmp = 1
        TMbkg = 1
        if item[1] == "smp":
            data_2d = sample_data[item[0]]
            normValue = TMsmp
        elif item[1] == "bkg":
            data_2d = background_data[item[0]]
            normValue = TMbkg
        else:
            data_2d = subtracted_data[item[0]]
            normValue = 1
        if monitor_002:
            normValue *= data_2d.info["civi"]


        q, intensity, err = data_2d.integrate_image(
            ai, q_bins, chi_start, chi_end, mask, normValue
        )

        corr_data = Data_1d(
            data_2d.dir,
            data_2d.ext,
            "1D~" + data_2d.name.split("~")[1],
            q,
            intensity,
            err,
            data_2d.info,
        )
        export_data_signal.emit(corr_data)
        exported += 1
        if self.canceled != True:
            progress_signal.emit(int((exported / len(names_types)) * 100))
        
        cancel_signal.connect(self.cancel_thread)
        
        # if self.batch_mode:
        #     self.batchmode_data.emit(corr_data)
        # else:
        #     self.data_name.emit("Processed: " + corr_data.name)

    # only plot last one
    # if not self.batch_mode:
    #     self.plot_data.emit(corr_data)

def mask_pix_zero(image, mask):
        inv_mask = np.abs(1 - mask)
        masked_image = np.multiply(image, inv_mask)
        return masked_image
    
def subtract_2d(self,
        export_data_signal,
        cancel_signal,
        progress_signal,
        data_name,
        smp_names,  
        smp_data, 
        bkg_dataset,
        mask, 
        scale, 
        smp_TM, 
        bkg_TM,
        bit_depth
        ):

    exported = 0
    self.canceled = False

    if mask is not None:
        bkg_dataset = mask_pix_zero(bkg_dataset.array, mask)
    else:
        bkg_dataset = bkg_dataset.array

    for item in smp_names:
        # TODO allow changing scale factor and civi
        scale_factor = 1
        civi_smp = 1
        civi_bkg = 1

        if mask is not None:
            smp_dataset = mask_pix_zero(smp_data[item.data()].array, mask)
        else:
            smp_dataset = smp_data[item.data()].array

        part1 = np.divide(
                smp_dataset * scale, smp_TM * civi_smp
            )

        part2 = np.divide(
                bkg_dataset * scale, bkg_TM * civi_bkg
            )
        
        out = np.subtract(part1, part2)
        if bit_depth == 8:
            out = out.astype(np.int8)
        elif bit_depth == 16:
            out = out.astype(np.int16)
        else:
            out = out.astype(np.int32)

        subd_data = Data_2d(
            smp_data[item.data()].dir,
            smp_data[item.data()].ext,
            "2D~" + "subd_" + smp_data[item.data()].name.split("~")[1],
            out,
            {"type": "sub"},
        )
        export_data_signal.emit(subd_data)
        exported += 1
        if self.canceled != True:
            progress_signal.emit(int((exported / len(smp_names)) * 100))
        cancel_signal.connect(self.cancel_thread)

def export_data(self,
            export_data_signal,
            cancel_signal,
            progress_signal,
            data_name,
            sample_data,
            background_data,
            subtracted_data,
            names_types,
            bit_depth,
            batch_mode,):
    
    
    exported = 0    
    self.canceled = False
    for item in names_types:
        if self.canceled:
            return
        data = get_data(item[0], item[1], sample_data, background_data, subtracted_data)
        if isinstance(data, Data_1d):
            export_single_dat(data, batch_mode)
        elif isinstance(data, Data_2d):
            export_single_image(data, bit_depth, batch_mode)
        elif isinstance(data, Data_1d_az):
            export_1d_az(data)
        exported += 1
        if self.canceled != True:
            progress_signal.emit(int((exported / len(names_types)) * 100))
        
        cancel_signal.connect(self.cancel_thread)

def get_data(name, dat_type, sample_data, background_data, subtracted_data):
    if dat_type == "smp":
        return sample_data[name]
    elif dat_type == "bkg":
        return background_data[name]
    else:
        return subtracted_data[name]

def export_1d_az(data):
    path = os.path.join(
        data.dir, data.name.split("~")[1] + "_azimuthal_" + "." + data.ext
    )
    if os.path.exists(path):
        path = append_file(path)

        #TODO: add warning message box
        # self.show_warning_messagebox(
        #     "File " + old_path + " found, saving to " + path
        # )
    np.savetxt(
        path, np.transpose([data.chi, data.intensity]), fmt="%1.6e", delimiter="    "
    )

def export_single_dat(data, batch_mode):
    if not batch_mode:
        path = os.path.join(data.dir, data.name.split("~")[1] + ".dat")
        if os.path.exists(path):
            old_path = path
            path = append_file(path)
            #TODO: add warning message box
            # self.show_warning_messagebox(
            #     "File " + old_path + " found, saving to " + path
            # )
        np.savetxt(
            path,
            np.transpose([data.q, data.intensity, data.err]),
            fmt="%1.6e",
            delimiter="    ",
        )
    else:
        if not os.path.exists(os.path.join(data.dir, "batch_processed")):
            os.mkdir(os.path.join(data.dir, "batch_processed"))

        path = os.path.join(
            data.dir, "batch_processed", data.name.split("~")[1] + ".dat"
        )
        np.savetxt(
            path,
            np.transpose([data.q, data.intensity, data.err]),
            fmt="%1.6e",
            delimiter="    ",
        )

def export_single_image(data, bit_depth, batch_mode):
    if bit_depth == 32:
        data.array = data.array.astype("int32")
    elif bit_depth == 16:
        data.array = data.array.astype("int16")
    elif bit_depth == 8:
        data.array = data.array.astype("int8")
    if not batch_mode:
        path = os.path.join(
            data.dir, data.name.split("~")[1] + "." + "tif"
        )  # always save as tif
        if os.path.exists(path):
            old_path = path
            path = append_file(path)
            
            #TODO: add warning message box
            # self.show_warning_messagebox(
            #     "File " + old_path + " found, saving to " + path
            # )
        tifffile.imwrite(path, data.array, dtype=data.array.dtype)
    else:
        if not os.path.exists(os.path.join(data.dir, "batch_processed")):
            os.mkdir(os.path.join(data.dir, "batch_processed"))
        path = os.path.join(
            data.dir, "batch_processed", data.name.split("~")[1] + "." + "tif"
        )
        tifffile.imwrite(path, data.array, dtype=data.array.dtype)

class Worker(QThread):
    export_data_signal = pyqtSignal(object)
    cancel_signal = pyqtSignal(bool)
    progress_signal = pyqtSignal(int)
    data_name = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super(Worker,self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
    
    @pyqtSlot()
    def run(self):
        self.fn(
            self,
            self.export_data_signal,
            self.cancel_signal,
            self.progress_signal,
            self.data_name,
            *self.args
        )
        #self.cancel_signal.connect(self.cancel_thread)

    def cancel_thread(self, val):
        if val is True:
            self.canceled = True
            
def append_file(path):
        counter = 0
        base_path = os.path.dirname(path)
        ext = os.path.basename(path).split(".")[-1]
        name = Path(path).stem
        if os.path.exists(path):
            # check if number suffix already:
            suff = name.split("_")[-1]

            if suff.isnumeric():
                counter = int(suff)
                pref = name.split("_")[:-1]
                pref = "".join(map(str, pref))
            else:
                counter = 0
                pref = name

            while True:
                counter += 1

                new_name = pref + "_" + str(counter)
                new_path = os.path.join(base_path, new_name + "." + ext)
                if os.path.exists(new_path):
                    continue
                else:
                    path = new_path
                    break
        return path
        
def import_data(
        self,
        export_data_signal,
        cancel_signal,
        progress_signal,
        data_name,
        fnames,
        data_type,
        fit2d_mode,
        monitor_002
    ):
    exported = 0
    self.canceled = False
    time.sleep(0.1)
    for item in fnames:
        if self.canceled:
            self.deleteLater()
            return
        

        if item.split(".")[-1] == "tif":
            data = Data_2d(
                os.path.dirname(item),
                os.path.basename(item).split(".")[-1],
                "2D~" + Path(item).stem,
                tifffile.imread(item),
                {"type": data_type},
            )

            if fit2d_mode:
                data.array = np.flipud(data.array)

            export_data_signal.emit(data)
            data_name.emit(data.name)
            del data

        elif item.split(".")[-1] == "h5":
            if monitor_002:
                civi, rigi, exp_time = readHeaderFile(
                    os.path.dirname(item), Path(item).stem[0:3]
                )
            
            imgData = fabio.open(item)
            for num in range(imgData.nframes):
                temp = {
                    "dir": os.path.dirname(item),
                    "ext": os.path.basename(item).split(".")[-1],
                    "name": "2D~" + Path(item).stem + "_" + str(num),
                    "info": {"type": data_type},
                }
                if imgData.nframes > 1:
                    temp["data"] = imgData.getframe(num).data

                else:
                    temp["data"] = imgData.data
                if monitor_002:
                    temp["info"]["civi"] = civi[num]
                    temp["info"]["rigi"] = rigi[num]
                    temp["info"]["expTime"] = exp_time[num]

                data = Data_2d(
                    temp["dir"],
                    temp["ext"],
                    temp["name"],
                    temp["data"],
                    temp["info"],
                )
                if fit2d_mode:
                    data.array = np.flipud(data.array)
                export_data_signal.emit(data)
                data_name.emit("Imported: " + data.name)
                del temp, data
        
        elif item.split(".")[-1] == "dat":
            try:
                raw_data = np.loadtxt(item, usecols=(0, 1, 2))
                data = Data_1d(
                    os.path.dirname(item),
                    os.path.basename(item).split(".")[-1],
                    "1D~" + Path(item).stem,
                    raw_data[:, 0],
                    raw_data[:, 1],
                    {"type": data_type},
                    err=raw_data[:, 2],
                )
                export_data_signal.emit(data)
                data_name.emit("Imported: " + data.name)
                del data
            except Exception as e:
                print(e)

        exported += 1
        if not self.canceled:
            progress_signal.emit(int((exported / len(fnames)) * 100))
        cancel_signal.connect(self.cancel_thread)

# class WorkerSignals(QtCore.QObject):
#     '''
#     Defines the signals available from a running worker thread.

#     Supported signals are:

#     finished
#         No data

#     error
#         tuple (exctype, value, traceback.format_exc() )

#     result
#         object data returned from processing, anything

#     progress
#         int indicating % progress

#     '''
#     finished = QtCore.pyqtSignal()
#     error = QtCore.pyqtSignal(tuple)
#     result = QtCore.pyqtSignal(object)
#     progress = QtCore.pyqtSignal(int)

# class Worker(QtCore.QRunnable):
#     '''
#     Worker thread

#     Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

#     :param callback: The function callback to run on this worker thread. Supplied args and
#                      kwargs will be passed through to the runner.
#     :type callback: function
#     :param args: Arguments to pass to the callback function
#     :param kwargs: Keywords to pass to the callback function

#     '''

#     def __init__(self, fn, *args, **kwargs):
#         super(Worker, self).__init__()

#         # Store constructor arguments (re-used for processing)
#         self.fn = fn
#         self.args = args
#         self.kwargs = kwargs
#         self.signals = WorkerSignals()

#         # Add the callback to our kwargs
#         self.kwargs['progress_callback'] = self.signals.progress

#     @pyqtSlot()
#     def run(self):
#         '''
#         Initialise the runner function with passed args, kwargs.
#         '''

#         # Retrieve args/kwargs here; and fire processing using them
#         try:
#             result = self.fn(*self.args, **self.kwargs)
#         except:
#             traceback.print_exc()
#             exctype, value = sys.exc_info()[:2]
#             self.signals.error.emit((exctype, value, traceback.format_exc()))
#         else:
#             self.signals.result.emit(result)  # Return the result of the processing
#         finally:
#             self.signals.finished.emit()  # Done
