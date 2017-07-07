from __future__ import print_function
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
        ''' Get the basename from the filename

        @param[in] filename The filename
        @return The basename
        xxx finish writing this docstring
        '''
        phuInfo, infoList = ParseTask.getInfo(self, filename)

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
        phuInfo['basename'] = basename
        #
        # Now pull the acq type & jobID from the path (no, they're not in the header)
        #
        pathComponents = pathname.split("/")
        if len(pathComponents) < 0:
            raise RuntimeError("Path %s is too short to deduce raftID" % pathname)
        raftId, runId, acquisitionType, testVersion, jobId, sensorLocationInRaft = pathComponents[-6:]
        if runId != phuInfo['run']:
            raise RuntimeError("Expected runId %s, found %s from path %s" % phuInfo['run'], runId, pathname)

        phuInfo['raftId'] = raftId # also in the header - RAFTNAME
        phuInfo['field'] = acquisitionType # NOT in the header
        phuInfo['jobId'] = int(jobId) #  NOT in the header, but do we need it?
        phuInfo['raft'] = 'R00' # do we need this?
        phuInfo['ccd'] = sensorLocationInRaft # NOT in the header

        return phuInfo, infoList

    def translate_wavelength(self, md):
        '''Translate wavelength provided by teststand readout.

        The teststand driving script asks for a wavelength, and then reads the value back to ensure that
        the correct position was moved to. This number is therefore read back with sub-nm precision.
        Typically the position is within 0.005nm of the desired position, so we warn if it's not very
        close to an integer value.

        Future users should be aware that the HIERARCH MONOCH-WAVELENG key is NOT the requested value, and
        therefore cannot be used as a cross-check that the wavelength was close to the one requested.
        The only record of the wavelength that was set is in the original filename.

        @param[in] md image metadata
        @return The recorded wavelength as an int
        '''
        raw_wl = md.get("MONOWL")
        wl = int(round(raw_wl))
        if abs(raw_wl-wl)>=0.1:
            logger = lsstLog.Log.getLogger('obs.comCam.ingest')
            logger.warn('Translated signigicatly non-integer wavelength %s', raw_wl)
        return wl

    def translate_visit(self, md):
        """Generate a unique visit from the timestamp

        It might be better to use the 1000*runNo + seqNo, but the latter isn't currently set
        @param[in] md image metadata
        @return Visit number, as translated
        """
        mjd = md.get("MJD-OBS")
        mmjd = mjd - 55197              # relative to 2010-01-01, just to make the visits a tiny bit smaller
        return int(1e5*mmjd)            # 86400s per day, so we need this resolution

##############################################################################################################

class ComCamCalibsParseTask(CalibsParseTask):
    """Parser for calibs"""

    def _translateFromCalibId(self, field, md):
        """Get a value from the CALIB_ID written by constructCalibs"""
        data = md.get("CALIB_ID")
        match = re.search(".*%s=(\S+)" % field, data)
        return match.groups()[0]

    def translate_ccd(self, md):
        return self._translateFromCalibId("ccd", md)

    def translate_filter(self, md):
        return self._translateFromCalibId("filter", md)

    def translate_calibDate(self, md):
        return self._translateFromCalibId("calibDate", md)
