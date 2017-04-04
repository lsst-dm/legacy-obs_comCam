from lsst.obs.comCam.ingest import ComCamParseTask

config.parse.retarget(ComCamParseTask)
config.parse.translation = {
    'expTime': 'EXPTIME',
    'object': 'OBJECT',
    'imageType': 'IMGTYPE',
    'testType': 'TESTTYPE',
    'filter': 'FILTER',
    'lsstSerial': 'LSST_NUM',
    'date': 'DATE-OBS',
    'dateObs': 'DATE-OBS',
    'run': 'RUNNUM',
}
config.parse.translators = {
    'visit': 'translate_visit',
}
config.parse.defaults = {
    'object': "UNKNOWN",
}
config.parse.hdu = 1

config.register.columns = {
    'run': 'text',
    'visit': 'int',
    'basename': 'text',
    'filter': 'text',
    'dateObs': 'text',
    'expTime': 'double',
    'raft': 'text',
    'ccd': 'int',
    'object': 'text',
    'imageType': 'text',
    'testType': 'text',
    'lsstSerial': 'text',
    'field': 'text',
}
config.register.visit = list(config.register.columns.keys())
