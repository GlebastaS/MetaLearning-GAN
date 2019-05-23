from os import listdir
from os.path import isfile, join
import os
import shutil

if __name__ == '__main__':
    path = f"../processed_data/dprocessed_16_64_2/"
    test_path = f"../processed_data/dtest/"
    count = 0
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    for i, name in enumerate(onlyfiles):
        if i % 10 == 0 and count < 911:
            count += 1
            os.rename(f"{path}{name}", f"{test_path}{name}")

