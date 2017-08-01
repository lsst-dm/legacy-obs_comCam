from lsst.obs.comCam.ingest import ComCamCalibsParseTask
config.parse.retarget(ComCamCalibsParseTask)

config.register.columns = {'filter': 'text',
                           'ccd': 'text',
                           'calibDate': 'text',
                           'validStart': 'text',
                           'validEnd': 'text',
                           }

config.parse.translators = {'ccd': 'translate_ccd',
                            'filter': 'translate_filter',
                            'calibDate': 'translate_calibDate',
                            }

config.register.unique = ['filter', 'ccd', 'calibDate']
config.register.tables = ['bias', 'dark', 'flat', 'fringe']
config.register.visit = ['calibDate', 'filter']
