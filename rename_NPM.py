import os

path1 = os.getcwd()

for r, d, f in os.walk(path1):
    for filename in f:
        if "NPM" in filename:
            print(r)
            newname = filename.replace("NPM", "PMSMF")
            os.rename(os.path.join(r, filename), os.path.join(r, newname))
