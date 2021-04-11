import math

import bsc_v2
import unittest

from parameterized import parameterized
from gi.repository import Nautilus, GObject
from bsc_v2 import convert, RESOLUTION_UNIT


if __name__ == '__main__':
    unittest.main()


class Test(unittest.TestCase):
    def test_get_resolution_unit(self):
        self.assertEqual(convert(RESOLUTION_UNIT, '2'), 'Inch', 'Unexpected resolution unit.')

    @parameterized.expand([
        ['None', None, ''],
        ['Empty', '', ''],
        ['Random text', 'some text', ''],
        ['Charset text', 'charset="Ascii" ', ''],
        ['Old pattern', 'charset="Ascii" sharpness=0.123456789', '0.123456789'],
        ['Json double quote', 'charset="Ascii" {"sharpness" : "0.123456789"}', '0.123456789'],
        ['Json two keys', 'charset="Ascii" {"key" : "value", "sharpness" : "0.123456789"}', '0.123456789'],
        ['Json single quote', 'charset="Ascii" {\'sharpness\' : 0.123456789}', ''],
        ['Prefix Json', 'charset="Ascii" Prefix {"sharpness" : "0.123456789"}', ''],
        ['Postfix Json', 'charset="Ascii" {"sharpness" : "0.123456789"} Postfix', ''],
        ['Other Json', 'charset="Ascii" {"key" : "value"}', 'not set'],
        ['Empty Json', 'charset="Ascii" {}', 'not set'],
    ])
    def test_extract_sharpness(self, testname, input, expected):
        self.assertEqual(expected, bsc_v2.extract_sharpness(input))

    @parameterized.expand([
        ['Negative', -1, '☆☆☆☆☆'],
        ['Zero', 0, '☆☆☆☆☆'],
        ['One', 1, '★☆☆☆☆'],
        ['Four', 4, '★★★★☆'],
        ['Five', 5, '★★★★★'],
        ['Six', 6, '★★★★★'],
        ['Float', 3.5, '★★★☆☆'],
        ['Real', math.pi, '★★★☆☆'],
        ['Inf', math.inf, '☆☆☆☆☆'],
        ['None', None, '☆☆☆☆☆'],
        ['Alphanumeric', '5', '★★★★★'],
        ['Alpha', 'a', '☆☆☆☆☆'],
    ])
    def test_as_stars(self, testname, input, expected):
        self.assertEqual(expected, bsc_v2.as_stars(input))

    @parameterized.expand([
        ['None', None, 'Error'],
        ['Empty', '', 'Error'],
        ['Seconds', 10, '00:00:10'],
        ['Minutes', 1000, '00:16:40'],
        ['Hours', 10000, '02:46:40'],
        ['>99 Hours', 100*60*60+100, '100:01:40'],
        ['Alphanumeric', '12345', '03:25:45'],
        ['Float', 3.5, '00:00:03'],
        ['Real', math.pi, '00:00:03'],
        ['Inf', math.inf, 'Error'],
        ['Alpha', 'a', 'Error'],
    ])
    def test_sec_to_time_format(self, testname, input, expected):
        self.assertEqual(expected, bsc_v2.sec_to_time_format(input))



class DummyFileInfoProvider(GObject.GObject, Nautilus.FileInfo):
    actual = {}

    def __init__(self, uri, mime_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri = uri
        self.mime_type = mime_type
        self.actual = {}

    def add_string_attribute(self, attribute_name, value):
        self.actual[attribute_name] = value

    def get_uri(self):
        return self.uri

    def get_uri_scheme(self):
        return 'file'

    def get_mime_type(self):
        return self.mime_type

    def is_mime_type(self, mime_type):
        return mime_type == self.mime_type


class TestColumnExtension(unittest.TestCase):
    EMPTY_VALUES = {k: '' for k in [d['name'] for d in bsc_v2.COLUMN_DEFINITIONS]}

    def setUp(self):
        self.maxDiff = None

    @parameterized.expand([
        ['image-JPG', 'resources/CanonEOS70D.jpg', 'image/jpg', {'aperture_value': '458752/65536', 'artist': 'exiftool.js', 'datetime_original': '2013:03:25 15:27:13', 'exposure_bias_value': '-1/3', 'exposure_mode': 'Auto exposure', 'exposure_time': '1/320', 'flash': 'Auto mode', 'fnumber': '11.0', 'focal_length': '12.0', 'gps_altitude': '0.0', 'gps_latitude': '0.0', 'gps_longitude': '0.0', 'iso_speed': '100', 'metering_mode': 'Pattern', 'model': 'Canon EOS 70D', 'orientation': '180º', 'resolution_unit': 'Inch', 'shutter_speed_value': '548864/65536', 'title': 'Sample image from exiftool.js', 'usercomment': 'charset="Ascii" sharpness=0.55', 'sharpness': '0.55', 'xresolution': '72/1', 'yresolution': '72/1', 'rating': '☆☆☆☆☆', 'width': '8', 'height': '8'}],
        ['audio-MP3', 'resources/gs-16b-2c-44100hz.mp3', 'audio/mpeg', {'title': 'Galway', 'artist': 'Kevin MacLeod'}],
        ['video-MP4', 'resources/gs-16b-2c-44100hz.mp4', 'video/mp4', {'duration': '00:00:15', 'format': 'MPEG-4', 'overall_bitrate': '130860', 'frame_count': '683', 'audio_format': 'AAC'}],
        ['audio-WMA', 'resources/gs-16b-2c-44100hz.wma', 'audio/x-ms-wma', {'duration': '00:00:15', 'format': 'Windows Media', 'overall_bitrate': '139387', 'bit_depth': '16', 'audio_format': 'WMA'}],
        ['doc-PDF', 'resources/sample.pdf', 'application/pdf', {'title': 'This is the Title', 'artist': 'Happy Woman', 'width': '216', 'height': '280', 'pages': '2'}],
    ])
    def test_update_file_info(self, testname, file, mime_type, non_empty_expected):
        # Set up required objects
        fileinfo = DummyFileInfoProvider('file://' + file, mime_type)
        bsc_v2.ColumnExtension.update_file_info(bsc_v2.ColumnExtension(), file=fileinfo)

        # Remove keys with default values from actual to visualize the difference in the message easier.
        non_empty_actual = {k: v for k, v in fileinfo.actual.items() if v is not ''}

        # Extend the expected values with empty values for other keys.
        self.assertEqual(non_empty_actual, non_empty_expected, msg=f"\nSummary:\nexpected: {non_empty_expected}\nactual  : {non_empty_actual}")