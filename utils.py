import math


def convert_size(size):
    if size <= 0:
        return "0 kb"
    size_name = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    i = size // 1024 ** (int(round(math.log(size, 1024))) - 1)
    d = round(size % 1024, 2)
    f = size_name[int(round(math.log(size, 1024))) - 1]
    return f"{d} {f}" if i == 0 else f"{i}.{d} {f}"
