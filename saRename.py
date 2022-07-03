import os
base = "accounts"
for count, file in enumerate(os.listdir(base)):
    abspath = os.path.join(base,file)
    destpath = os.path.join(base,f"{count}.json")
    os.rename(abspath,destpath)