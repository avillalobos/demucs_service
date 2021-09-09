#!/usr/bin/python3

from typing import Optional
import graphene
import logging
import lib.utils as utils
from lib.demucs_service import DemucsService


class DemucsServiceAPI(graphene.ObjectType):
    split = graphene.String(
        description="This function will trigger a song split based "
        "on received parameters",
        song=graphene.String(required=True),
        model=graphene.String(),
        device=graphene.String(),
        start_time=graphene.String(),
        end_time=graphene.String()
    )

    split_from_url = graphene.String(
        description="This function will trigger a song split based "
        "on a youtube video",
        url=graphene.String(required=True),
        model=graphene.String(),
        device=graphene.String(),
        start_time=graphene.String(),
        end_time=graphene.String()
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
        song: str,
        model: str = "demucs",
        device: str = 'cpu',
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        demucs_srv = DemucsService(model, device)
        # rather than having a long lasting request,
        # we should have a job created
        logging.info(f"running demucs with {model} and {device}")
        final_song_name = song
        if start_time and end_time:
            final_song_name = utils.trim_song(song, start_time, end_time)
        demucs_srv.split_song(final_song_name)
        logging.info('demucs completed')
        return (
            "Song has been separated succesfully!"
            " url generated: www.demucs.com/download/"
            f"{utils.get_download_link(final_song_name, model)}"
        )

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
        url: str,
        model: str = "demucs",
        device: str = 'cpu',
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        try:
            logging.info(
                f"Received a split from url, trying to fetch video \
                from Youtube {url} - {model} - {device}"
            )
            filename = utils.video_to_mp3(url)
            if not filename:
                raise Exception("Failed to convert video to mp4")
            demucs_srv = DemucsService(model, device)
            # rather than having a long lasting request,
            # we should have a job created
            logging.info(f"running demucs with {model} and {device}")
            final_song_name = filename
            if start_time and end_time:
                final_song_name = utils.trim_song(
                    filename,
                    start_time,
                    end_time
                )
            demucs_srv.split_song(final_song_name)
            logging.info('demucs completed')
            # filename is the full path to the downloaded song,
            # we only need the basename for the song
            try:
                return (
                    "Song has been separated succesfully!"
                    " url generated: www.demucs.com/download/"
                    f"{utils.get_download_link(final_song_name, model)}"
                )
            except Exception as e:
                return f"Something went wrong: {e}"

        except Exception as e:
            return f"Something went bananas {e}"
