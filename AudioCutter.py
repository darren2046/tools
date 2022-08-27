from bagbag import * # pip install bagbag 

args = (
    Tools.Argparser().
        Add("src", "source mp3 file"). 
        Add("txt", "rule file to cut the mp3").
        Add("dst", "directory to output mp3"). 
        Get()
)

for i in filter(lambda x: x != "", [i.strip() for i in open(args.txt)]):
    name, start, end = i.split("|")
    if start == "" or end == "":
        continue 

    Lg.Trace(name, start, end)

    duration = Time.Strptime("%H:%M:%S", end) - Time.Strptime("%H:%M:%S", start)
    if duration < 0:
        Lg.Error("持续时间不能小于0", exc=False)
        continue

    cmd = f"ffmpeg -ss {start} -t {duration} -i '{args.src}' -acodec copy '{args.dst}/{name}.mp3'"

    Lg.Trace(cmd)
    Os.System(cmd)