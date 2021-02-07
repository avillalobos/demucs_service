#!/usr/bin/python3

import base64
import graphene
import logging
import lib.utils as utils

from datetime import datetime
from pathlib import Path
from lib.demucs_service import DemucsService


class DemucsServiceAPI(graphene.ObjectType):
    split = graphene.String(
        description="This function will trigger a song split based "
        "on received parameters",
        song=graphene.String(required=True),
        model=graphene.String(),
        device=graphene.String()
    )

    split_from_url = graphene.String(
        description="This function will trigger a song split based "
        "on a youtube video",
        url=graphene.String(required=True),
        model=graphene.String(),
        device=graphene.String()
    )

    list_songs = graphene.List(
        graphene.String,
        description="This endpoint will return a list of songs"
        " availables on the service (useful when downloading"
        " youtube videos. Ideally the UI will do a download video"
        " request followed by a list_songs based on the name"
        " based on the name returned by download youtube video",
    )

    list_separated_songs = graphene.List(
        graphene.String,
        description="This endpoint will return all the songs"
        " that were already separated and availabe on the server."
        " By default it will return all the songs under demucs",
        model=graphene.String()
    )

    music_from_video = graphene.String(
        description="This endpoint will download the MP3 version"
        " of a youtube video and will store it on the songs directory"
        " of the session",
        url=graphene.String(required=True)
    )

    def resolve_split(
        self,
        info,
        song,
        model="demucs",
        device='cpu'
    ):
        demucs_srv = DemucsService(model, device)
        # rather than having a long lasting request,
        # we should have a job created
        logging.info(f"running demucs with {model} and {device}")
        demucs_srv.split_song(song)
        logging.info('demucs completed')
        return "Job <JOBID> has been created"

    def resolve_music_from_video(self, info, url):
        try:
            filename = utils.video_to_mp3(url)
            return filename
        except Exception as e:
            return f"Something went wrong when downloading the video {e}"

    def resolve_list_songs(self, info):
        try:
            return utils.list_songs('songs')
        except Exception as e:
            return f"Something went wrong when trying to list songs {e}"

    def resolve_list_separated_songs(self, info, model='demucs'):
        try:
            return utils.list_songs(f"separated/{model}")
        except Exception as e:
            return [f"Something went wrong, unable to return songs: {e}"]

    def resolve_split_from_url(
        self,
        info,
        url,
        model="demucs",
        device='cpu'
    ):
        try:
            logging.info(
                f"Received a split from url, trying to fetch video \
                from Youtube {url} - {model} - {device}"
            )
            filename = utils.video_to_mp3(url)
            demucs_srv = DemucsService(model, device)
            # rather than having a long lasting request,
            # we should have a job created
            logging.info(f"running demucs with {model} and {device}")
            demucs_srv.split_song(filename)
            logging.info('demucs completed')
            # filename is the full path to the downloaded song,
            # we only need the basename for the song
            download = utils.zip_files(model, Path(filename).stem)
            download_url = base64.standard_b64encode(
                str(datetime.today()).encode()
            )
            utils.create_new_download(str(download), download_url.decode())
            return f"Song has been separated succesfully!, \
                url generated: www.demucs.com/download/{download_url.decode()}"

        except Exception as e:
            return f"Something went bananas {e}"
