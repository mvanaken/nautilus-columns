# Contributing to plugin

## Adding columns
You can add your own columns with information of your choice.
1. Include a column within COLUMN_DEFINITIONS dict on top of the script.
    * Choose a name, label and description, all three are required.
    * Remember the name
1. Determine the mime_type of the type of files, if it is a new one.
   ```bash
   mimetype <file>
   ```
1. Start a new section with a nice header, e.g.
    ```
    ################
    # pdf handling #
    ################
    ```
1. Add an if-clause within `update_file_info` for the new `mime-type`, or continue with an existing one, e.g.
    ```python
    if file.is_mime_type('application/pdf'):
    ```
1. Always start a try-except for a new block, so when an exception occurs in this new part, it will not break the functionality of the rest.
1. Prefer to use `with open(filename) as variablename:` when opening the file.
1. Create a new object.
1. Map values from the new object to `file` using one of the mapping methods. The most generic one is `map_any`
    ```python
    map_any(file, bbox, 'height', f=lambda b: self.points_from_bbox(b, 1), c=self.points_to_mm)
    ```
    See the javadoc for more information.
1. Include a test within `test_bsc_v2.py`
    * Add a file under test/resources
    * Extend the parameterized test with the new resource. e.g.
        ```json
        ['audio-MP3', 'resources/gs-16b-2c-44100hz.mp3', 'audio/mpeg', {'title': 'Galway', 'artist': 'Kevin MacLeod'}],
        ```
        * The first parameter is just the test name, you can type there whatever you want.
        * The second is the relative path to the resource
        * The third is the mime-type of the file.
1. Run the test.
1. If all is green...profit!

## Generate language/translation files

* Create a language template file `messages.pot` with
    ```bash
    pygettext3 bsc_v2.py
    ```
* Install `gettext` if you do not have it installed
    ```bash
    sudo apt install gettext
    ```
* Then update existing translations with
    ```bash
    msgmerge message.pot <LANG>.po
    ```
* Create a new translation file with
    ```bash
    msginit -i messages.pot -l <LANG>
    ```
  
## Interesting reads

* http://www.bernaerts-nicolas.fr/linux/76-gnome/349-gnome-nautilus-exif-iptc-xmp-gps-column-property-extension
* https://lazka.github.io/pgi-docs/Nautilus-3.0/index.html