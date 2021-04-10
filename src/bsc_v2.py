#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of nautilus-columns

# this script can installed to the current user account by running the
# following commands:

# sudo apt-get install python-FileManager python-mutagen python-pyexiv2
# python-kaa-metadata

# mkdir ~/.local/share/FileManager-python/extensions/
# cp bsc_v2.py ~/.local/share/FileManager-python/extensions/
# chmod a+x ~/.local/share/FileManager-python/extensions/bsc_v2.py

# alternatively, you can be able to place the script in:
# /usr/share/FileManager-python/extensions/

# change log:
# geb666: original bsc.py, based on work by Giacomo Bordiga
# jmdsdf: version 2 adds extra ID3 and EXIF tag support
# jmdsdf: added better error handling for ID3 tags, added mp3 length support,
#         distinguished between exif image size and true image size
# SabreWolfy: set consistent hh:mm:ss format, fixed bug with no ID3 information
#             throwing an unhandled exception
# jmdsdf: fixed closing file handles with mpinfo (thanks gueba)
# jmdsdf: fixed closing file handles when there's an exception
#         (thanks Pitxyoki)
# jmdsdf: added video parsing (work based on enbeto, thanks!)
# jmdsdf: added FLAC audio parsing through kaa.metadata
#         (thanks for the idea l-x-l)
# jmdsdf: added trackno, added mkv file support (thanks ENigma885)
# jmdsdf: added date/album for flac/video (thanks eldon.t)
# jmdsdf: added wav file support thru pyexiv2
# jmdsdf: added sample rate file support thru mutagen and kaa
#         (thanks for the idea N'ko)
# jmdsdf: fix with tracknumber for FLAC, thanks l-x-l
# draxus: support for pdf files
# arun (engineerarun@gmail.com): made changes to work with naulitus 3.x
# Andrew@webupd8.org: get EXIF support to work with FileManager 3
# Julien Blanc: fix bug caused by missing Exif.Image.Software key
# Andreas Schönfelder: show stars as rating

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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import gi

try:
    gi.require_version('Nautilus', '3.0')
    gi.require_version('GObject', '2.0')
    gi.require_version('GExiv2', '0.10')
except ValueError as error:
    print(error)
    exit(1)
from gi.repository import Nautilus as FileManager
from gi.repository import GObject
from gi.repository import GExiv2

import urllib
# for id3 support
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MPEGInfo
# for reading image dimensions
from PIL import Image
# for reading pdf
from PyPDF2 import PdfFileReader
# for reading videos. for future improvement, this can also read mp3!
from plumbum import local
from plumbum import CommandNotFound
# locale
import sys
import os
import json
import math
import locale
import gettext

APP = 'nautilus-columns'
ROOTDIR = '/usr/share/'
LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')

try:
    current_locale, encoding = locale.getdefaultlocale()
    language = gettext.translation(APP, LANGDIR, [current_locale])
    language.install()
    if sys.version_info[0] == 3:
        _ = language.gettext
    else:
        _ = language.ugettext
except Exception as e:
    print(e)
    _ = str

RESOLUTION_UNIT = {
    '1' : 'No absolute unit of measurement',
    '2' : 'Inch',
    '3' : 'Centimeter'
}
ORIENTATION = {
    GExiv2.Orientation.NORMAL : 'Normal',
    GExiv2.Orientation.HFLIP : 'Flipped',
    GExiv2.Orientation.VFLIP : 'Flipped',
    GExiv2.Orientation.ROT_90_HFLIP : 'Flipped',
    GExiv2.Orientation.ROT_90_VFLIP : 'Flipped',
    GExiv2.Orientation.ROT_90 : '90º',
    GExiv2.Orientation.ROT_180 : '180º',
    GExiv2.Orientation.ROT_270 : '270º',
}
METERING_MODE = {
    '1' : 'Average',
    '2' : 'Center weighted average',
    '3' : 'Spot',
    '4' : 'Multi spot',
    '5' : 'Pattern',
    '6' : 'Partial',
    '255' : 'other ',
}
LIGHT_SOURCE = {
    '0': 'Unknown',
    '1': 'Daylight',
    '2' : 'Fluorescent',
    '3' : 'Tungsten (incandescent light)',
    '4' : 'Flash',
    '9' : 'Fine weather',
    '10' : 'Cloudy weather',
    '11' : 'Shade',
    '12' : 'Daylight fluorescent (D 5700 - 7100K)',
    '13' : 'Day white fluorescent (N 4600 - 5400K)',
    '14' : 'Cool white fluorescent (W 3900 - 4500K)',
    '15' : 'White fluorescent (WW 3200 - 3700K)',
    '17' : 'Standard light A',
    '18' : 'Standard light B',
    '19' : 'Standard light C',
    '20' : 'D55',
    '21' : 'D65',
    '22' : 'D75',
    '23' : 'D50',
    '24' : 'ISO studio tungsten',
    '255' : 'Other light source',
}
EXPOSURE_MODE = {
    '0': 'Auto exposure',
    '1': 'Manual exposure',
    '2': 'Auto bracket',
}
GAIN_CONTROL = {
    '0': 'None',
    '1': 'Low Gain Up',
    '2': 'High Gain Up',
    '3': 'Low Gain Down',
    '4': 'High Gain Down',
}
FLASH = {
    '0': 'Flash did not fire',
    '1': 'Flash fired',
    '2': 'Strobe return light detected',
    '4': 'Strobe return light not detected',
    '8': 'Compulsory flash mode',
    '16': 'Auto mode',
    '32': 'No flash function',
    '64': 'Red eye reduction mode',
}
COLUMN_DEFINITIONS = [
    # Media
    { 'name' : 'title', 'label': 'Title', 'description': 'Song title'},
    { 'name' : 'album', 'label': 'Album', 'description': 'Album'},
    { 'name' : 'artist', 'label': 'Artist', 'description': 'Artist'},
    { 'name' : 'tracknumber', 'label': 'Track', 'description': 'Track number'},
    { 'name' : 'genre', 'label': 'Genre', 'description': 'Genre'},
    { 'name' : 'date', 'label': 'Date', 'description': 'Date'},
    { 'name' : 'bitrate', 'label': 'Bitrate', 'description': 'Audio Bitrate in kilo bits per second'},
    { 'name' : 'samplerate', 'label': 'Sample rate', 'description': 'Sample rate in Hz'},
    { 'name' : 'length', 'label': 'Length', 'description': 'Length of audio'},
    # Images
    { 'name' : 'exposure_time', 'label': 'Exposure time', 'description': 'Exposure time in seconds'},
    { 'name' : 'fnumber', 'label': 'F number', 'description': 'Exposure F number'},
    { 'name' : 'focal_length', 'label': 'Focal length', 'description': 'The actual focal length of the lens, in mm.'},
    { 'name' : 'gps_altitude', 'label': 'Altitude', 'description': 'GPS Altitude'},
    { 'name' : 'gps_latitude', 'label': 'Latitude', 'description': 'GPS Latitude'},
    { 'name' : 'gps_longitude', 'label': 'Longitude', 'description': 'GPS Longitude'},
    { 'name' : 'iso_speed', 'label': 'ISO', 'description': 'ISO Speed'},
    { 'name' : 'orientation', 'label': 'Orientation', 'description': 'Orientation'},
    { 'name' : 'model', 'label': 'Model', 'description': 'Model'},
    { 'name' : 'resolution_unit', 'label': 'Resolution unit', 'description': 'The unit for measuring'},
    { 'name' : 'xresolution', 'label': 'X resolution', 'description': 'The resolution in the x axis'},
    { 'name' : 'yresolution', 'label': 'Y resolution', 'description': 'The resolution in the y axis'},
    { 'name' : 'datetime_original', 'label': 'Capture date', 'description': 'Photo capture date'},
    { 'name' : 'shutter_speed_value', 'label': 'Shutter speed', 'description': 'Shutter speed'},
    { 'name' : 'aperture_value', 'label': 'Aperture', 'description': 'The lens aperture'},
    { 'name' : 'brightness_value', 'label': 'Brightness', 'description': 'Brightness'},
    { 'name' : 'exposure_bias_value', 'label': 'Exposure', 'description': 'The exposure bias'},
    { 'name' : 'max_aperture_value', 'label': 'Max aperture', 'description': 'The smallest F number of the lens'},
    { 'name' : 'metering_mode', 'label': 'Metering mode', 'description': 'The metering mode'},
    { 'name' : 'light_source', 'label': 'Light source', 'description': 'The kind of light source'},
    { 'name' : 'flash', 'label': 'Flash', 'description': 'Indicates the status of flash when the image was shot'},
    { 'name' : 'exposure_mode', 'label': 'Exposure mode', 'description': 'The exposure mode set when the image was shot'},
    { 'name' : 'gain_control', 'label': 'Gain control', 'description': 'The degree of overall image gain adjustment'},
    { 'name' : 'width', 'label': 'Width', 'description': 'Image/video/pdf width (pixel/mm)'},
    { 'name' : 'height', 'label': 'Height', 'description': 'Image/video/pdf height (pixel/mm)'},
    { 'name' : 'pages', 'label': 'Pages', 'description': 'Number of pages'},
    { 'name' : 'usercomment', 'label': 'UserComment', 'description': 'Comment of the user'},
    { 'name' : 'duration', 'label': 'Duration', 'description': 'Duration of the media file'},
    { 'name' : 'format', 'label': 'Format', 'description': 'Format of the media file'},
    { 'name' : 'overall_bitrate', 'label': 'Overall ', 'description': 'Overall bitrate of the media file'},
    { 'name' : 'frame_count', 'label': 'Frame count', 'description': 'Number of frames in video file'},
    { 'name' : 'video_format', 'label': 'Video format', 'description': 'Format of the video'},
    { 'name' : 'bit_depth', 'label': 'Bit depth', 'description': 'Bit depth of the media file'},
    { 'name' : 'audio_format', 'label': 'Audio format', 'description': 'Format of the audio'},
    { 'name' : 'sharpness', 'label': 'Sharpness', 'description': 'Sharpness of subject in image file'},
]

def convert(dict, value):
    return dict.get(value, 'Unknown')

# [SabreWolfy] added consistent formatting of times in format
# hh:mm:ss
# [SabreWolfy[ to allow for correct column sorting by length
# [MvA] moved to separate method for reusability
def secToTimeFormat(secondsInFloat):
    seconds = int(float(secondsInFloat))
    return f'{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d}'



MAIN_PATTERN=re.compile('charset="Ascii" (?P<dict>.*)')
OLD_PATTERN=re.compile('sharpness=(?P<sharpness>.*)')
def extract_sharpness(v):
    if v is None:
        return ''
    match = MAIN_PATTERN.match(v)
    if match:
        v = match.group('dict')
    match = OLD_PATTERN.match(v)
    if match:
        return match.group('sharpness')
    try:
        return json.loads(v).get('sharpness', 'not set')
    except Exception as e:
        return ''

def map_exif(file, metadata, field, tag=None, c=lambda v:v, f=lambda m,t:m.get_tag_string(t)):
    map_any(file, metadata, field, f=lambda m: f(m, tag), c=c)

def map_audio(file, audio, field):
    map_any(file, audio, field, f=lambda a:a.get(field, [''])[0])

def map_mediainfo(file, metadata, field, tag, c=lambda v:v):
    map_any(file, metadata, field, f=lambda m:m.get(tag), c=c)

def map_any(file, info_element, field,  f, c=lambda v:v):
    """
    Map any object to the columns. This is a separate method so we can handle exceptions for every mapping equally.
    This also allows for a generic check to see if the field matches with any name in COLUMN_DEFINITIONS. If it is not,
    a warning is printed.

    :param file: the Nautilus FilInfo object.
    :param info_element: the object holding the values to show in nautilus.
    :param field: the name of the column to map the value to, should be the same name as defined within COLUMN_DEFINITIONS.
    :param f: the function how to extract the value from info_element.
    :param c: the converter function how to convert the value.
    :return: nothing
    """
    try:
        if field not in [c['name'] for c in COLUMN_DEFINITIONS]:
            print(f"WARNING! Setting attribute for {field}, but there is no corresponding Column defined.")
        value = f(info_element)
        if value is not None:
            convertedValue = c(value)
            file.add_string_attribute(field, _(str(convertedValue)))
    except Exception:
        file.add_string_attribute(field, _('Error'))


class MediaInfo:
    """
    MediaInfo extracts the mediainfo values into a single dict:
        metadata = MediaInfo('multimedia-file.mov')
    Elements can be extracted using `get`.
    Available elements can be retrieved using 'keys'.
    """

    def __init__(self, path_to_video):
        self.path_to_video = path_to_video

        try:
            mediainfo = local['mediainfo']
        except CommandNotFound:
            raise IOError('mediainfo not found.')

        if os.path.isfile(path_to_video):
            options = ['--Output=JSON', '-f', path_to_video]
            data = json.loads(mediainfo(options))
            self.merged_data = {}
            # Merge all metadata to one dict.
            for metadata in data['media']['track']:
                # Avoid that Format is overwritten, this is the only key that occurs within the different tracks.
                if metadata['@type'] == 'Video':
                    self.merged_data['VideoFormat'] = metadata.get('Format', _('Unknown'))
                elif metadata['@type'] == 'Audio':
                    self.merged_data['AudioFormat'] = metadata.get('Format', _('Unknown'))
                self.merged_data = {**metadata, **self.merged_data}

    def get(self, key):
        return self.merged_data.get(key, '')

    def keys(self):
        return list(self.merged_data.keys())


class ColumnExtension(GObject.GObject,
                      FileManager.ColumnProvider,
                      FileManager.InfoProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_columns(self):
        return [self.jsonToColumn(column) for column in COLUMN_DEFINITIONS]

    @staticmethod
    def jsonToColumn(dict):
        name = dict.get('name')
        return FileManager.Column(name=f'NautilusPython::{name}_column',
                                  attribute=name,
                                  label=_(dict.get('label')),
                                  description=_(dict.get('description')))

    def update_file_info(self, file, **kwargs):
        if file.get_uri_scheme() != 'file':
            return

        # Set defaults to blank, else values are showing 'unknown' instead.
        [file.add_string_attribute(column.get('name'), '') for column in COLUMN_DEFINITIONS]

        # strip file:// to get absolute path
        filename = urllib.parse.unquote_plus(file.get_uri()[7:])

        ################
        # mp3 handling #
        ################
        if file.is_mime_type('audio/mpeg'):
            # attempt to read ID3 tag
            try:
                audio = EasyID3(filename)
                map_audio(file, audio, 'title')
                map_audio(file, audio, 'album')
                map_audio(file, audio, 'artist')
                map_audio(file, audio, 'tracknumber')
                map_audio(file, audio, 'genre')
                map_audio(file, audio, 'date')
            except Exception:
                pass

            # try to read MP3 information (bitrate, length, samplerate)
            with open(filename) as mpfile:
                try:
                    mpinfo = MPEGInfo(mpfile)
                    map_any(file, mpinfo, 'bitrate',    f=lambda m: m.bitrate / 1000, c=lambda v: v + ' Kbps')
                    map_any(file, mpinfo, 'samplerate', f=lambda m: m.sample_rate,    c=lambda v: v + ' Hz')
                    map_any(file, mpinfo, 'length',     f=lambda m: m.length,         c=secToTimeFormat)
                except Exception:
                    pass

        ##################
        # image handling #
        ##################
        if file.get_mime_type().split('/')[0] in ('image'):
            try:
                metadata = GExiv2.Metadata(filename)
            except Exception:
                metadata = GExiv2.Metadata()

            map_exif(file, metadata, 'aperture_value', 'Exif.Photo.ApertureValue')
            map_exif(file, metadata, 'artist', 'Exif.Image.Artist')
            map_exif(file, metadata, 'brightness_value', 'Exif.Photo.BrightnessValue')
            map_exif(file, metadata, 'datetime_original', 'Exif.Image.DateTime')
            map_exif(file, metadata, 'exposure_bias_value', 'Exif.Photo.ExposureBiasValue')
            map_exif(file, metadata, 'exposure_mode', 'Exif.Photo.ExposureMode', c=lambda v: convert(EXPOSURE_MODE, v))
            map_exif(file, metadata, 'exposure_time', f=lambda m,t: m.get_exposure_time())
            map_exif(file, metadata, 'flash', 'Exif.Photo.Flash', c=lambda v: convert(FLASH, v))
            map_exif(file, metadata, 'fnumber',       f=lambda m,t: m.get_fnumber())
            map_exif(file, metadata, 'focal_length',  f=lambda m,t: m.get_focal_length())
            map_exif(file, metadata, 'gain_control', 'Exif.Photo.GainControl', c=lambda v: convert(GAIN_CONTROL, v))
            map_exif(file, metadata, 'gps_altitude',  f=lambda m,t: m.get_gps_altitude())
            map_exif(file, metadata, 'gps_latitude',  f=lambda m,t: m.get_gps_latitude())
            map_exif(file, metadata, 'gps_longitude', f=lambda m,t: m.get_gps_longitude())
            map_exif(file, metadata, 'iso_speed',     f=lambda m,t: m.get_iso_speed())
            map_exif(file, metadata, 'light_source', 'Exif.Photo.LightSource', c=lambda v: convert(LIGHT_SOURCE, v))
            map_exif(file, metadata, 'max_aperture_value', 'Exif.Photo.MaxApertureValue')
            map_exif(file, metadata, 'metering_mode', 'Exif.Photo.MeteringMode', c=lambda v: convert(METERING_MODE, v))
            map_exif(file, metadata, 'model', 'Exif.Image.Model')
            map_exif(file, metadata, 'orientation',   f=lambda m,t:m.get_orientation(), c=lambda v: convert(ORIENTATION, v))
            map_exif(file, metadata, 'resolution_unit', 'Exif.Image.ResolutionUnit', c=lambda v: convert(RESOLUTION_UNIT, v))
            map_exif(file, metadata, 'shutter_speed_value', 'Exif.Photo.ShutterSpeedValue')
            map_exif(file, metadata, 'title', 'Exif.Image.ImageDescription')
            map_exif(file, metadata, 'usercomment', 'Exif.Photo.UserComment')
            map_exif(file, metadata, 'sharpness', 'Exif.Photo.UserComment', c=extract_sharpness)
            map_exif(file, metadata, 'xresolution', 'Exif.Image.XResolution')
            map_exif(file, metadata, 'yresolution', 'Exif.Image.YResolution')

            try:
                im = Image.open(filename)
                map_any(file, im, 'width', f=lambda i: i.size[0])
                map_any(file, im, 'height', f=lambda i: i.size[1])
            except Exception:
                pass

        #######################
        # video/flac handling #
        #######################
        if file.is_mime_type('video/x-msvideo') or\
                file.is_mime_type('video/mpeg') or\
                file.is_mime_type('video/x-ms-wmv') or\
                file.is_mime_type('audio/x-ms-wma') or\
                file.is_mime_type('video/mp4') or\
                file.is_mime_type('audio/x-flac') or\
                file.is_mime_type('video/x-flv') or\
                file.is_mime_type('video/x-matroska') or\
                file.is_mime_type('audio/x-wav'):
            try:
                mediainfo = MediaInfo(filename)
                map_mediainfo(file, mediainfo, 'format', 'Format')
                map_mediainfo(file, mediainfo, 'duration', 'Duration', c=secToTimeFormat)
                map_mediainfo(file, mediainfo, 'overall_bitrate', 'OverallBitRate')
                map_mediainfo(file, mediainfo, 'frame_count', 'FrameCount')
                map_mediainfo(file, mediainfo, 'video_format', 'VideoFormat')
                map_mediainfo(file, mediainfo, 'width', 'Width')
                map_mediainfo(file, mediainfo, 'height', 'Height')
                map_mediainfo(file, mediainfo, 'bit_depth', 'BitDepth')
                map_mediainfo(file, mediainfo, 'audio_format', 'AudioFormat')
            except Exception:
                pass

        ################
        # pdf handling #
        ################
        if file.is_mime_type('application/pdf'):
            try:
                with open(filename, 'rb') as f:
                    pdf = PdfFileReader(f)
                    map_any(file, pdf, 'pages', f=lambda i:i.getNumPages())

                    info = pdf.getDocumentInfo()
                    map_any(file, info, 'title', f=lambda i:i.title)
                    map_any(file, info, 'artist', f=lambda i:i.author)

                    if pdf.getNumPages() > 0:
                        bbox = pdf.getPage(0).mediaBox
                        map_any(file, bbox, 'width', f=lambda b: self.points_from_bbox(b, 0), c=self.points_to_mm)
                        map_any(file, bbox, 'height', f=lambda b: self.points_from_bbox(b, 1), c=self.points_to_mm)
            except Exception:
                pass

    def points_from_bbox(self, bbox, index):
        return abs(bbox.upperRight[index] - bbox.lowerLeft[index])

    def points_to_mm(self, pt):
        return int(float(pt) * math.sqrt(2.0) / 4.0)

