#!/usr/bin/python3


import graphene

from lib.demucs_service import DemucsService
from lib.utils import (
    video_to_mp3,
    list_songs
)


class DemucsServiceAPI(graphene.ObjectType):
    hello = graphene.String(description='A typical hello world')
    split = graphene.String(
        description="This function will trigger a song split based "
        "on received parameters",
        song=graphene.String(required=True),
        model_path=graphene.String(),
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

    def resolve_hello(self, info):
        print("executing resolve")
        return 'World'

    def resolve_split(
            self,
            info,
            song,
            model_path="lib/demucs/models/demucs.th",
            device='cpu'
    ):
        demucs_srv = DemucsService(model_path, device)
        # rather than having a long lasting request,
        # we should have a job created
        print(f"running demucs with {model_path} and {device}")
        demucs_srv.split_song(song)
        print('demucs completed')
        return "Job <JOBID> has been created"

    def resolve_music_from_video(self, info, url):
        try:
            filename = video_to_mp3(url)
            return f"Video {filename} downloaded successfully"
        except Exception as e:
            return f"Something went wrong when downloading the video {e}"

    def resolve_list_songs(self, info):
        try:
            return list_songs('songs')
        except Exception as e:
            return f"Something went wrong when trying to list songs {e}"

    def resolve_list_separated_songs(self, info, model='demucs'):
        try:
            return list_songs(f"separated/{model}")
        except Exception as e:
            return [f"Something went wrong, unable to return songs: {e}"]
