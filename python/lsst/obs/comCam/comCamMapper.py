#
# LSST Data Management System
# Copyright 2016 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#


import lsst.afw.image.utils as afwImageUtils
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
from lsst.obs.base import CameraMapper
import lsst.pex.policy as pexPolicy

from lsst.obs.comCam import ComCam

__all__ = ["ComCamMapper"]


class ComCamMapper(CameraMapper):
    packageName = 'obs_comCam'

    def __init__(self, inputPolicy=None, **kwargs):
        policyFile = pexPolicy.DefaultPolicyFile(self.packageName, "comCamMapper.paf", "policy")
        policy = pexPolicy.Policy(policyFile)

        CameraMapper.__init__(self, policy, policyFile.getRepositoryPath(), **kwargs)

        # Ensure each dataset type of interest knows about the full range of keys available from the registry
        keys = {'visit': int,
                'ccd': int,
                'filter': str,
                'date': str,
                'expTime': float,
                'object': str,
                'imageType': str,
                }
        for name in ("raw", "raw_amp",
                     # processCcd outputs
                     "postISRCCD", "calexp", "postISRCCD", "src", "icSrc", "srcMatch",
                     ):
            self.mappings[name].keyDict.update(keys)

        self.filterIdMap = {}           # where is this used?  Generating objIds??

        afwImageUtils.defineFilter('NONE', 0.0, alias=['no_filter', "OPEN"])

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry
        """
        return ComCam()

    def ___extractDetectorName(self, dataId):
        return "0"

    def ___computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier with visit
        """
        visit = dataId['visit']
        return int(visit)

    def __validate(self, dataId):
        visit = dataId.get("visit")
        if visit is not None and not isinstance(visit, int):
            dataId["visit"] = int(visit)
        return dataId

    def ___setCcdExposureId(self, propertyList, dataId):
        propertyList.set("Computed_ccdExposureId", self._computeCcdExposureId(dataId))
        return propertyList

    def __bypass_defects(self, datasetType, pythonType, location, dataId):
        """ since we have no defects, return an empty list.  Fix this when defects exist """
        return [afwImage.DefectBase(afwGeom.Box2I(afwGeom.Point2I(x0, y0), afwGeom.Point2I(x1, y1))) for
                x0, y0, x1, y1 in (
                    # These may be hot pixels, but we'll treat them as bad until we can get more data
                    (3801, 666, 3805, 669),
                    (3934, 582, 3936, 589),
        )]

    def ___defectLookup(self, dataId):
        """ This function needs to return a non-None value otherwise the mapper gives up
        on trying to find the defects.  I wanted to be able to return a list of defects constructed
        in code rather than reconstituted from persisted files, so I return a dummy value.
        """
        return "this_is_a_hack"

    # def __bypass_raw(self, datasetType, pythonType, location, dataId):
    #     """Read raw image with hacked metadata"""
    #     filename = location.getLocations()[0]
    #     md = self.bypass_raw_md(datasetType, pythonType, location, dataId)
    #     image = afwImage.DecoratedImageU(filename)
    #     image.setMetadata(md)
    #     return self.std_raw(image, dataId)

    def __bypass_raw_md(self, datasetType, pythonType, location, dataId):
        """Read metadata for raw image, adding fake Wcs"""
        filename = location.getLocations()[0]
        md = afwImage.readMetadata(filename, 1)  # 1 = PHU
        return md

    # bypass_raw_amp = bypass_raw
    # bypass_raw_amp_md = bypass_raw_md

    def __standardizeCalib(self, dataset, item, dataId):
        """Standardize a calibration image read in by the butler

        Some calibrations are stored on disk as Images instead of MaskedImages
        or Exposures.  Here, we convert it to an Exposure.

        @param dataset  Dataset type (e.g., "bias", "dark" or "flat")
        @param item  The item read by the butler
        @param dataId  The data identifier (unused, included for future flexibility)
        @return standardized Exposure
        """
        mapping = self.calibrations[dataset]
        if "MaskedImage" in mapping.python:
            exp = afwImage.makeExposure(item)
        elif "Image" in mapping.python:
            if hasattr(item, "getImage"):  # For DecoratedImageX
                item = item.getImage()
            exp = afwImage.makeExposure(afwImage.makeMaskedImage(item))
        elif "Exposure" in mapping.python:
            exp = item
        else:
            raise RuntimeError("Unrecognised python type: %s" % mapping.python)

        parent = super(CameraMapper, self)
        if hasattr(parent, "std_" + dataset):
            return getattr(parent, "std_" + dataset)(exp, dataId)
        return self._standardizeExposure(mapping, exp, dataId)

    def __std_bias(self, item, dataId):
        return self.standardizeCalib("bias", item, dataId)

    def __std_dark(self, item, dataId):
        exp = self.standardizeCalib("dark", item, dataId)
        # exp.getCalib().setExptime(1.0)
        return exp

    def __std_flat(self, item, dataId):
        return self.standardizeCalib("flat", item, dataId)

    def __std_fringe(self, item, dataId):
        return self.standardizeCalib("flat", item, dataId)
