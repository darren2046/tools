from bagbag import *

if __name__ == "__main__":
    dirpath = Os.Args[1]

    for fname in Os.ListDir(dirpath):
        if fname.startswith("Resized_"):
            continue 

        if len(Re.FindAll("IMG_[0-9]+.JPG", fname)) == 0:
            continue 

        src = Os.Path.Join(dirpath, fname)
        dst = Os.Path.Join(dirpath, f"Resized_{fname}")

        if Os.Path.Exists(dst):
            continue 
        
        Lg.Info(f"Resizing {fname} to Resized_{fname}")
        Funcs.ResizeImage(src, dst, 1920, quality=80)

