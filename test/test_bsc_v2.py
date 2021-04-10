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
        ['image-JPG', 'resources/CanonEOS70D.jpg', 'image/jpg', {'title': 'Sample image from exiftool.js', 'artist': 'exiftool.js', 'exposure_time': '1/320', 'fnumber': '11.0', 'focal_length': '12.0', 'gps_altitude': '0.0', 'gps_latitude': '0.0', 'gps_longitude': '0.0', 'iso_speed': '100', 'orientation': '180º', 'model': 'Canon EOS 70D', 'resolution_unit': 'Inch', 'xresolution': '72/1', 'yresolution': '72/1', 'datetime_original': '2013:03:25 15:27:13', 'shutter_speed_value': '548864/65536', 'aperture_value': '458752/65536', 'exposure_bias_value': '-1/3', 'metering_mode': 'Pattern', 'flash': 'Auto mode', 'exposure_mode': 'Auto exposure', 'width': '8', 'height': '8'}],
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
        expected = {**self.EMPTY_VALUES, **non_empty_expected}
        actual = fileinfo.actual
        self.assertEqual(actual, expected, msg=f"\nSummary:\nexpected: {non_empty_expected}\nactual  : {non_empty_actual}")