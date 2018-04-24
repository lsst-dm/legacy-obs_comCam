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
import os
import sys
import unittest

import lsst.utils.tests
from lsst.afw.coord import IcrsCoord
import lsst.ip.isr
from lsst.utils import getPackageDir
from lsst.afw.geom import Extent2I
import lsst.obs.base.tests
import lsst.obs.comCam


class TestObsComCam(lsst.obs.base.tests.ObsTests, lsst.utils.tests.TestCase):
    def setUp(self):
        product_dir = getPackageDir('testdata_comCam')
        repo_dir = os.path.join(product_dir, 'repo')
        calib_dir = os.path.join(product_dir, 'repo')

        butler = lsst.daf.persistence.Butler(root=repo_dir, calibRoot=calib_dir)
        mapper = lsst.obs.comCam.ComCamMapper(root=repo_dir)
        visit = 269921586  # this is a 77s 1000nm flat
        filt = '550CutOn'
        ccd = 0
        dataIds = {'raw': {'visit': visit, 'ccd': ccd},
                   'bias': {'visit': visit, 'ccd': ccd},
                   'dark': {'visit': visit, 'ccd': ccd},
                   'flat': {'visit': visit, 'ccd': ccd}
                   }
        self.setUp_tests(butler, mapper, dataIds)

        ccdExposureId_bits = 32
        exposureIds = {'raw': 180804850, 'bias': 180804850, 'dark': 180804850, 'flat': 180804850}
        filters = {'raw': '550CutOn', 'bias': 'NONE', 'dark': 'NONE', 'flat': '550CutOn'}
        exptimes = {'raw': 30.0, 'bias': 0.0, 'dark': 1.0, 'flat': 0.0}
        detectorIds = {'raw': ccd, 'bias': ccd, 'dark': ccd, 'flat': ccd}
        detector_names = {'raw': '1_12', 'bias': '1_12', 'dark': '1_12', 'flat': '1_12'}
        detector_serials = {'raw': '50', 'bias': '50', 'dark': '50', 'flat': '50'}
        dimensions = {'raw': Extent2I(4096, 4004),
                      'bias': Extent2I(4096, 4004),
                      'dark': Extent2I(4096, 4004),
                      'flat': Extent2I(4096, 4004)
                      }
        sky_origin = IcrsCoord('21:22:59.982', '+00:30:00.07')
        raw_subsets = (({'level': 'ccd', 'filter': '550CutOn'}, 1),
                       ({'level': 'ccd', 'visit': visit}, 1),
                       ({'level': 'filter', 'visit': visit}, 1),
                       ({'level': 'visit', 'filter': '550CutOn'}, 1),
                       ({'level': 'visit', 'filter': '550CutOn'}, 0)
                       )
        good_detectorIds = tuple(range(0, 111))
        bad_detectorIds = (112, 113)
        linearizer_type = lsst.ip.isr.LinearizeSquared.LinearityType
        ccd_key_name = "ccd"
        self.setUp_butler_get(ccdExposureId_bits=ccdExposureId_bits,
                              exposureIds=exposureIds,
                              filters=filters,
                              exptimes=exptimes,
                              detectorIds=detectorIds,
                              detector_names=detector_names,
                              detector_serials=detector_serials,
                              dimensions=dimensions,
                              sky_origin=sky_origin,
                              raw_subsets=raw_subsets,
                              good_detectorIds=good_detectorIds,
                              bad_detectorIds=bad_detectorIds,
                              linearizer_type=linearizer_type,
                              ccd_key_name=ccd_key_name
                              )

        raw_filename = 'HSC-0904024-050.fits'
        path_to_raw = os.path.join(repo_dir, "STRIPE82L/2013-11-02/00671/HSC-I", raw_filename)
        keys = set(('calibDate', 'ccd', 'dateObs', 'field', 'filter', 'name',
                    'patch', 'pointing', 'pixel_id', 'stack', 'tract', 'visit',
                    'style', 'description', 'subfilter'))
        query_format = ["visit", "filter"]
        queryMetadata = (({'visit': visit}, [(visit, '550CutOn')]),
                         ({'filter': '550CutOn'}, [(visit, '550CutOn')]),
                         )
        map_python_type = 'lsst.afw.image.DecoratedImageU'
        map_cpp_type = 'DecoratedImageU'
        map_storage_name = 'FitsStorage'
        metadata_output_path = 'processCcd_metadata/v%s_f%s.boost'%(visit, filters['raw'])
        default_level = 'sensor'
        raw_levels = (('skyTile', {'filter': str, 'pointing': int,
                                   'taiObs': str, 'field': str,
                                   'dateObs': str, 'expTime': float}),
                      ('tract', {'expTime': float, 'taiObs': str,
                                 'pointing': int, 'field': str,
                                 'filter': str, 'ccd': int,
                                 'dateObs': str, 'visit': int}),
                      ('visit', {'expTime': float, 'taiObs': str,
                                 'pointing': int, 'field': str,
                                 'filter': str, 'dateObs': str,
                                 'visit': int}),
                      ('sensor', {'expTime': float, 'taiObs': str,
                                  'pointing': int, 'field': str,
                                  'filter': str, 'ccd': int,
                                  'dateObs': str, 'visit': int})
                      )
        self.setUp_mapper(output=repo_dir,
                          path_to_raw=path_to_raw,
                          keys=keys,
                          query_format=query_format,
                          queryMetadata=queryMetadata,
                          metadata_output_path=metadata_output_path,
                          map_python_type=map_python_type,
                          map_cpp_type=map_cpp_type,
                          map_storage_name=map_storage_name,
                          raw_filename=raw_filename,
                          default_level=default_level,
                          raw_levels=raw_levels,
                          )

        self.setUp_camera(camera_name='ComCam',
                          n_detectors=9,
                          first_detector_name='S00',
                          camera_size=Extent2I(4096, 4004)  # This test will break for ITL chips
                          )

        super(TestObsComCam, self).setUp()


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    setup_module(sys.modules[__name__])
    unittest.main()
