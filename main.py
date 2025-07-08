#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import re
import time
import asyncio
import requests

import value
from value import download_path
from color import color
from utils import convert_size
from animeme import Anime_Me_Season, Anime_Me_Episode
from animeone import Anime_One_Season, Anime_One_Episode


async def main():
    start_time = time.time()

    if not os.path.exists(download_path):
        os.mkdir(download_path)

    anime_urls = open("url.txt", "r").read().splitlines()

    for anime_url in anime_urls:
        url_list = []
        is_Animeme = True
        # 區分連結類型
        if re.search(r"anime1.me/category/(.*?)", anime_url, re.M | re.I) or re.search(
            r"anime1.me/\?cat=[0-9]", anime_url, re.M | re.I
        ):
            url_list.extend(await Anime_Me_Season(anime_url))
        elif re.search(r"anime1.me/\d+", anime_url, re.M | re.I):
            url_list.append(anime_url)
        elif re.search(r"https://anime1\.one/\d+-\d+", anime_url, re.I):
            is_Animeme = False
            url_list.append(anime_url)
        elif re.search(r"https://anime1\.one/\d+/?$", anime_url, re.I):
            is_Animeme = False
            url_list.extend(await Anime_One_Season(anime_url))

        else:
            color.RED.format(
                "-", "Unable to support this link. QAQ ({})".format(anime_url)
            )
            continue

        folder = url_list.pop(-1)

        for url in url_list[::-1]:
            if is_Animeme:
                await Anime_Me_Episode(folder, url)
            else:
                await Anime_One_Episode(folder, url)

    end_time = time.time()
    print(
        f"+ 耗時 {round(end_time - start_time, 2)} 秒, 下載 {value.eps} 集, 總大小 {convert_size(value.total_size)}"
    )


if __name__ == "__main__":
    asyncio.run(main())
