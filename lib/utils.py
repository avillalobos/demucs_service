#!/usr/bin/python3

from pathlib import Path
from pytube import YouTube
from moviepy.editor import VideoFileClip


# TODO make sure to return mp3, this will return mp4
def video_to_mp3(url):
    video_filename = YouTube(
        url
    ).streams.filter(
        progressive=True, 
        file_extension='mp4'
    ).order_by('resolution').desc().first().download(output_path='songs')
    return mp4_to_mp3(video_filename)


def mp4_to_mp3(video_filename):
    video_path = Path(video_filename)
    video = VideoFileClip(str(video_path))
    mp3_filename = f"songs/{video_path.name.replace('mp4', 'mp3')}"
    video.audio.write_audiofile(mp3_filename)
    video_path.unlink()
    return mp3_filename


def list_songs(path):
    return [s for s in Path(path).iterdir()]
