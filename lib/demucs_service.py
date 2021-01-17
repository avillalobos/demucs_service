#!/usr/bin/python3

import sys

from lib.demucs import demucs
from lib.demucs.demucs import model
from lib.demucs.demucs.audio import AudioFile
from lib.demucs.demucs.utils import apply_model, load_model
from pathlib import Path
from scipy.io import wavfile


# within the demucs directory
sys.modules['demucs.model'] = model
sys.modules['demucs'] = demucs


class DemucsService():

    def __init__(self, model_path, device):
        # This will require all the parameters to build and split the song.

        # Get from the arguments the model that we want to use,
        # by default demucs
        self.model_path = model_path

        # Get the device that we want to use to split the song, by default cpu
        self.device = device  # it can be cuda if NVIDIA available

        # Number of random shifts for equivariant stabilization.
        # Increase separation time but improves quality for Demucs. 10 was used
        self.shifts = 0

        # Apply the model to the entire input at once rather than
        # first splitting it in chunks of 10 seconds
        self.split = True

        # This hack is to be able to load a pickled class from
        self.model = load_model(self.model_path)

        # default location for the service
        self.out = Path('separated/demucs')
        self.out.mkdir(parents=True, exist_ok=True)
        # default tracks:
        self.source_names = ["drums", "bass", "other", "vocals"]

        self.mp3_bitrate = 320

    """
    def encode_mp3(wav, path, bitrate=320, verbose=False):
        try:
            import lameenc
        except ImportError:
            print("Failed to call lame encoder. Maybe it is not installed? "
                "On windows, run `python.exe -m pip install -U lameenc`, "
                "on OSX/Linux, run `python3 -m pip install -U lameenc`, "
                "then try again.", file=sys.stderr)
            sys.exit(1)
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(bitrate)
        encoder.set_in_sample_rate(44100)
        encoder.set_channels(2)
        encoder.set_quality(2)  # 2-highest, 7-fastest
        if not verbose:
            encoder.silence()
        mp3_data = encoder.encode(wav.tostring())
        mp3_data += encoder.flush()
        with open(path, "wb") as f:
            f.write(mp3_data)
    """

    def split_song(self, track_path):
        track = Path(track_path)
        wav = AudioFile(track).read(
            streams=0, samplerate=44100, channels=2).to(self.device)
        wav = (wav * 2**15).round() / 2**15
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()
        sources = apply_model(self.model, wav, shifts=self.shifts,
                              split=self.split, progress=True)
        sources = sources * ref.std() + ref.mean()

        track_folder = self.out / track.name.replace(track.suffix, '')
        track_folder.mkdir(exist_ok=True)
        for source, name in zip(sources, self.source_names):
            source = (source * 2**15).clamp_(-2**15, 2**15 - 1).short()
            source = source.cpu().transpose(0, 1).numpy()
            # I can't install lameenc so I'm skipping mp3 for now
            # stem = str(track_folder / name)
            # self.encode_mp3(source, stem + ".mp3", self.mp3_bitrate)
            wavname = str(track_folder / f"{name}.wav")
            wavfile.write(wavname, 44100, source)
