from lsst.obs.comCam.ingest import ComCamParseTask

config.parse.retarget(ComCamParseTask)
config.parse.translation = {
    'expTime': 'EXPTIME',
    'object': 'OBJECT',
    'imageType': 'IMGTYPE',
    'filter': 'FILTER',
    'lsstSerial': 'LSST_NUM',
    'date': 'DATE-OBS',
    'dateObs': 'DATE-OBS',
    'run': 'RUNNUM',
}
config.parse.translators = {
    #'ccd': 'translate_ccd',
    'visit': 'translate_visit',
    # 'date': 'translate_date',
}
config.parse.defaults = {
    'object': "UNKNOWN",
}
config.parse.hdu = 1

config.register.columns = {
    'visit': 'int',
    'basename': 'text',
    'filter': 'text',
    'dateObs': 'text',
    'expTime': 'double',
    'ccd': 'int',
    'object': 'text',
    'imageType': 'text',
    'lsstSerial': 'text',
    'field': 'text',
}
config.register.visit = list(config.register.columns.keys())
