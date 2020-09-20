import re
from zipfile import (ZipFile, ZIP_DEFLATED)
from io import BytesIO
import string_funcs
import json


def create_zip(data, user_data):
    """creates a zip from the data applyting user_data, and returns an in-memory file"""
    bio = BytesIO()
    zip_file = ZipFile(bio, "a", compression=ZIP_DEFLATED)

    # put user_data in variables
    lyrics_language = user_data['lyrics_lang']
    include_annotations = user_data['include_annotations']
    identifiers = ['!--!', '!__!']

    # set zip file name
    album_title = data['album_title']
    artist = data['artist']
    full_title = string_funcs.format_title(artist, album_title)
    full_title = string_funcs.format_filename(full_title)
    bio.name = f'{full_title}.zip'

    # Save the songs as text
    for i, song in enumerate(data['songs']):

        lyrics = song['lyrics']

        # format annotations
        lyrics = string_funcs.format_annotations(lyrics, song['annotations'],
                                                 include_annotations, identifiers)

        # formatting lyrics language
        lyrics = string_funcs.format_language(lyrics, lyrics_language)
        # newlines in text files inside zip files need to be
        # \r\n on Windows
        lyrics = lyrics.replace('\n', '\r\n')

        # cleaning title name
        title = song['title']
        title = re.sub(r'.*[\s]*-\s*', '', title)
        title = re.sub(r'[\s][\(\[][^\x00-\x7F]+.*[\)\]]', '', title)
        title = string_funcs.format_filename(title)

        # create lyrics file
        if i < 9:
            file_name = f'0{i+1} - {title}.txt'
        else:
            file_name = f'{i+1} - {title}.txt'
        zip_file.writestr(file_name, lyrics)
    zip_file.close()
    bio.seek(0)
    return bio


# driver code
def test(json_file, lyrics_language, include_annotations):
    with open(json_file) as f:
        data = json.load(f)
    user_data = {'lyrics_lang': lyrics_language, 'include_annotations': include_annotations}
    file = create_zip(data, user_data)
    with open('test.zip', 'wb') as f:
        f.write(file.getvalue())
