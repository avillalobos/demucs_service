#!/usr/bin/python3

import pathlib
from tube_dl import Youtube, extras

# TODO make sure to return mp3, this will return mp4
def video_to_mp3(url):
    video = Youtube(
        url
    ).formats.filter_by(
        only_audio=True
    )[0].download(path='songs')
    output = extras.Convert(video, 'mp3', add_meta=True)
    return output.file


def list_songs(path):
    return [s for s in pathlib.Path(path).iterdir()]
