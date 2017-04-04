from __future__ import print_function
import os
import re
from lsst.pipe.tasks.ingest import ParseTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask


EXTENSIONS = ["fits", "gz", "fz"]  # Filename extensions to strip off


class ComCamParseTask(ParseTask):
    """Parser suitable for comCam data

    See https://docushare.lsstcorp.org/docushare/dsweb/Get/Version-43119/FITS_Raft.pdf
    """

    def __init__(self, config, *args, **kwargs):
        super(ParseTask, self).__init__(config, *args, **kwargs)

    def getInfo(self, filename):
        # Grab the basename
        phuInfo, infoList = ParseTask.getInfo(self, filename)

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)
        phuInfo['basename'] = basename
        #
        # Now pull the sensor ID from the path (no, it's not in the header)
        #
        pathComponents = pathname.split("/")
        if len(pathComponents) < 0:
            raise RuntimeError("Path %s is too short to deduce raftID" % pathname)
        raftId, runId, acquisitionType, testVersion, jobId, sensorLocationInRaft = pathComponents[-6:]
        if runId != phuInfo['run']:
            raise RuntimeError("Expected runId %s, found %s from path %s" % phuInfo['run'], runId, pathname)

        phuInfo['raftId'] = raftId
        phuInfo['field'] = acquisitionType
        phuInfo['jobId'] = int(jobId)
        phuInfo['raft'] = 'R00'
        phuInfo['ccd'] = sensorLocationInRaft

        return phuInfo, infoList

    # Add entry to config.parse.translators in config/ingest.py if needed
    def translate_ccd(self, md):
        return md.get("sensorId")       # ... except that isn't actually present

    # Add an entry to config.parse.translators in config/ingest.py if needed
    def translate_visit(self, md):
        """Generate a unique visit from the timestamp

        It would be better to use the 1000*runNo + seqNo, but the latter isn't currently set
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
