from pydub import AudioSegment, silence
import time
from bagbag import *

args = (
    Tools.Argparser().
        Add("file", "mp3 file").
        Get()
)

def gt(t):
    return time.strftime("%H:%M:%S", time.gmtime(t))

song = AudioSegment.from_mp3(args.file)

s = silence.split_on_silence(song, keep_silence=True, silence_thresh=-60, min_silence_len=500, seek_step=1000)

Lg.Info("Total:", len(s))

c = 0

directory = args.file.rstrip(".mp3")
Os.Mkdir(directory)

for idx in Range(len(s)):
    path = Os.Path.Join(directory, f"{idx}.mp3")
    Lg.Trace(f"Saving to:{path}")
    s[idx].export(path)
