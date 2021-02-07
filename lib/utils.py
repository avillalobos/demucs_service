#!/usr/bin/python3

import logging
import os
from typing import Optional
from pathlib import Path
from pytube import YouTube
from moviepy.editor import VideoFileClip
from zipfile import ZipFile
import sqlite3


# TODO make sure to return mp3, this will return mp4
def video_to_mp3(url) -> str:
    video_filename: str = YouTube(
        url
    ).streams.filter(
        progressive=True, 
        file_extension='mp4'
    ).order_by('resolution').desc().first().download(output_path='songs')
    return mp4_to_mp3(video_filename)


def mp4_to_mp3(video_filename) -> str:
    video_path = Path(video_filename)
    video = VideoFileClip(str(video_path))
    mp3_filename = f"songs/{video_path.name.replace('mp4', 'mp3')}"
    video.audio.write_audiofile(mp3_filename)
    video_path.unlink()
    return mp3_filename


def list_songs(path):
    return [s for s in Path(path).iterdir()]


def zip_files(model, song) -> Optional[Path]:
    """
    This function will zip the content of song in model
    """
    song_path = Path('separated') / Path(model) / Path(song)
    download_path = Path('downloads') / Path(f'{song}.zip')
    # new zipfile will be located in the downloads folder
    try:
        with ZipFile(download_path, 'w') as archive:
            logging.debug(f"Creating archive zip file {archive}")
            with os.scandir(song_path) as target:
                logging.debug(f"Exploring song's directory {target}")
                # adding all the files inside the song's directory
                for f in target:
                    logging.debug(f"Adding {f} to {archive} ")
                    archive.write(
                        f.path,
                        arcname=f"{song}/{f.name}"
                    )
        logging.info("File compressions succesfully completed!")
        return download_path
    except Exception as e:
        logging.error(f"Semething went wrong when creating the zip file {e}")
        return None


def create_new_download(song_path, download_url) -> None:
    try:
        with sqlite3.connect('models/database.db') as db:
            db.execute(
                "INSERT INTO downloads (song_path, download_url, accessed) \
                values (?, ?, False)", (song_path, download_url,)
            )
            db.commit()
    except Exception as e:
        logging.error(f"There was an error when creating new download: {e}")


def disable_download(download_url: str) -> None:
    try:
        with sqlite3.connect('models/database.db') as db:
            db.execute(
                "UPDATE downloads SET accessed = True \
                WHERE download_url = ? AND accessed = False", (download_url,)
            )
            db.commit()
    except Exception as e:
        logging.debug(f"There was a problem when disabling the download: {e}")


def get_download_file(download_url: str) -> Optional[Path]:
    try:
        logging.debug(f"Attempting to retrieve file: {download_url}")
        with sqlite3.connect('models/database.db') as db:
            result = db.execute(
                "SELECT song_path \
                FROM downloads \
                WHERE download_url=? AND accessed=False",
                (download_url,)
            )
            song_path_row = result.fetchone()
            if song_path_row:
                logging.debug(f"got filepath: {song_path_row}")
                return Path(song_path_row[0])
            else:
                logging.debug("Download link not found")
                return None
    except Exception as e:
        logging.error(
            f"There was an error when retrieving the filename from the DB {e}"
        )
        return None


def remove_download_file(download_path: Path) -> None:
    try:
        if download_path:
            download_path.unlink()
        else:
            logging.warning("The received path is empty/None")
    except Exception as e:
        logging.error(
            f"There was a problem removing file: {download_path} - {e}"
        )
