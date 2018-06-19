from __future__ import division, print_function
import os
import re
from lsst.pipe.tasks.ingest import ParseTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask
import lsst.log as lsstLog

EXTENSIONS = ["fits", "gz", "fz"]  # Filename extensions to strip off


class ComCamParseTask(ParseTask):
    """Parser suitable for comCam data

    See https://docushare.lsstcorp.org/docushare/dsweb/Get/Version-43119/FITS_Raft.pdf
    """

    def __init__(self, config, *args, **kwargs):
        super(ParseTask, self).__init__(config, *args, **kwargs)

    def getInfo(self, filename):
        """ Get the basename and other data which is only available from the filename/path.

        This seems fragile, but this is how the teststand data will *always* be written out, 
        as the software has been "frozen" as they are now in production mode.

        Parameters
        ----------
        filename : `str`
            The filename

        Returns
        -------
        phuInfo : `dict`
            Dictionary containing the header keys defined in the ingest config from the primary HDU
        infoList : `list`
            A list of dictionaries containing the phuInfo(s) for the various extensions in MEF files
        """
        phuInfo, infoList = ParseTask.getInfo(self, filename)

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
        phuInfo['basename'] = basename

        # Now pull the acq type & jobID from the path (no, they're not in the header)
        # the acq type is the type of test, eg flat/fe55/darks etc
        # jobID is the test number, and corresponds to database entries in the eTraveller/cameraTestDB
        pathComponents = pathname.split("/")
        if len(pathComponents) < 0:
            raise RuntimeError("Path %s is too short to deduce raftID" % pathname)
        raftId, runId, acquisitionType, testVersion, jobId, sensorLocationInRaft = pathComponents[-6:]
        if runId != phuInfo['run']:
            raise RuntimeError("Expected runId %s, found %s from path %s" % phuInfo['run'], runId, pathname)

        phuInfo['raftId'] = raftId # also in the header - RAFTNAME
        phuInfo['field'] = acquisitionType # NOT in the header
        phuInfo['jobId'] = int(jobId) #  NOT in the header
        phuInfo['raft'] = 'R00'
        phuInfo['ccd'] = sensorLocationInRaft # NOT in the header

        return phuInfo, infoList

    def translate_wavelength(self, md):
        """Translate wavelength provided by teststand readout.

        The teststand driving script asks for a wavelength, and then reads the value back to ensure that
        the correct position was moved to. This number is therefore read back with sub-nm precision.
        Typically the position is within 0.005nm of the desired position, so we warn if it's not very
        close to an integer value.

        Future users should be aware that the HIERARCH MONOCH-WAVELENG key is NOT the requested value, and
        therefore cannot be used as a cross-check that the wavelength was close to the one requested.
        The only record of the wavelength that was set is in the original filename.

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        wavelength : `int`
            The recorded wavelength as an int
        """
        raw_wl = md.getScalar("MONOWL")
        wl = int(round(raw_wl))
        if abs(raw_wl-wl) >= 0.1:
            logger = lsstLog.Log.getLogger('obs.comCam.ingest')
            logger.warn(
                'Translated significantly non-integer wavelength; %s is more than 0.1nm from an integer value', raw_wl)
        return wl

    def translate_visit(self, md):
        """Generate a unique visit from the timestamp

        It might be better to use the 1000*runNo + seqNo, but the latter isn't currently set

        Parameters
        ----------
        md : `lsst.daf.base.PropertyList or PropertySet`
            image metadata

        Returns
        -------
        visit_num : `int`
            Visit number, as translated
        """
        mjd = md.getScalar("MJD-OBS")
        mmjd = mjd - 55197              # relative to 2010-01-01, just to make the visits a tiny bit smaller
        return int(1e5*mmjd)            # 86400s per day, so we need this resolution

##############################################################################################################


class ComCamCalibsParseTask(CalibsParseTask):
    """Parser for calibs"""

    def _translateFromCalibId(self, field, md):
        """Get a value from the CALIB_ID written by constructCalibs"""
        data = md.getScalar("CALIB_ID")
        match = re.search(".*%s=(\S+)" % field, data)
        return match.groups()[0]

    def translate_ccd(self, md):
        return self._translateFromCalibId("ccd", md)

    def translate_filter(self, md):
        return self._translateFromCalibId("filter", md)

    def translate_calibDate(self, md):
        return self._translateFromCalibId("calibDate", md)
