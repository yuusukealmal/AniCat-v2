import os
import re
import shutil

import requests
import urllib3
from bs4 import BeautifulSoup as bs4
from alive_progress import alive_bar

import value
from color import color

BASE = "https://anime1.one"


async def Anime_One_Season(url):
    if url.endswith("/"):
        url = url[:-1]
    urls = []
    r = requests.get(url, timeout=(3, 7))
    soup = bs4(r.text, "lxml")

    h2 = soup.find_all("h2", class_="entry-title")
    for i in h2:
        target = i.find("a", attrs={"rel": "bookmark"}).get("href")
        urls.append(BASE + target)

    # nextPage
    if soup.find("div", class_="nav-previous"):
        ele_div = soup.find("div", class_="nav-previous")
        nextUrl = ele_div.find("a").get("href")
        urls.extend(await Anime_One_Season(BASE + nextUrl))
    else:
        name = re.search(
            r"(.*?) \u2013 Anime1\.one 動畫線上看", soup.find("title").text, re.M | re.I
        ).group(1)
        if not os.path.exists(os.path.join(value.download_path, name)):
            os.mkdir(os.path.join(value.download_path, name))
        urls.append(name)
    return urls


def filter_m3u8(base, m3u8):
    lines = m3u8.splitlines()
    count = 0
    keep_lines = []
    for line in lines:
        if line.endswith(".ts") and line.split(".")[0].endswith(str(count).zfill(3)):
            keep_lines.append(base + line)
            count += 1

    return keep_lines


def mixed_ts(m3u8, folder, video_name):
    output_path = os.path.join(value.download_path, folder, f"{video_name}.mp4")
    with open(output_path, "wb") as output:
        for ts_file in m3u8:
            m3u8_path = os.path.join(
                value.download_path, folder, "temp", ts_file.split("/")[-1]
            )
            with open(m3u8_path, "rb") as seg:
                output.write(seg.read())
    value.eps += 1
    shutil.rmtree(os.path.join(value.download_path, folder, "temp"))


async def Anime_One_Episode(folder, url):
    if url.endswith("/"):
        url = url[:-1]
    episode_request = requests.get(url, timeout=(3, 7))
    soup = bs4(episode_request.text, "lxml")
    title = soup.find("meta", attrs={"property": "og:title"}).get("content")
    try:
        proxies = [
            BASE + button.get("url")
            for button in soup.find_all("button", class_="play-select")
        ]
        for i in proxies[1:]:
            proxy_request = requests.get(i)
            proxy_soup = bs4(proxy_request.text, "lxml")
            try:
                index_url = proxy_soup.find("source").get("src")
                mixed = requests.get(index_url, timeout=(3, 7)).text.splitlines()[-1]
                mixed_url = "/".join(index_url.rsplit("/", 1)[0:1]) + "/" + mixed
                mixed_m3u8 = requests.get(mixed_url).text
                break
            except (
                urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                requests.exceptions.SSLError,
            ) as e:
                color.YELLOW.format(
                    "-",
                    "Proxy Not Found For: {}: Cause: {}".format(i, e),
                )
        cleaned_m3u8 = filter_m3u8(
            "/".join(mixed_url.rsplit("/", 1)[0:1]) + "/", mixed_m3u8
        )
        await Anime_One_MP4_DL(cleaned_m3u8, folder, title)
    except Exception as e:
        color.RED.format(
            "x", "Error to find data for this link: {}, Cause: {}".format(url, e)
        )
        return


async def Anime_One_MP4_DL(m3u8, folder, video_name, retries=3):
    temp_folder = os.path.join(value.download_path, folder, "temp")
    os.makedirs(temp_folder, exist_ok=True)

    with alive_bar(
        len(m3u8), title=video_name, spinner="arrows2", bar="filling"
    ) as bar:
        for f in m3u8:
            ts_file = os.path.join(temp_folder, f.split("/")[-1])
            try:
                r = requests.get(f, timeout=(3, 7))
            except Exception as e:
                if retries > 0:
                    color.YELLOW.format(
                        "!", f"Retry to Download: {video_name}, Cause: {e}"
                    )
                    return await Anime_One_MP4_DL(m3u8, folder, video_name, retries - 1)
                else:
                    color.RED.format("x", f"Fail to Download: {video_name}, Cause: {e}")
                    return None

            content_length = int(r.headers.get("Content-Length", 0))
            if os.path.exists(ts_file) and os.path.getsize(ts_file) == content_length:
                bar()
                continue

            if r.status_code == 200:
                try:
                    with open(ts_file, "wb") as f_out:
                        f_out.write(r.content)
                    value.total_size += content_length
                except Exception as e:
                    color.RED.format("x", f"Download Error: {video_name}, Cause: {e}")
                    return await Anime_One_MP4_DL(m3u8, folder, video_name)
            else:
                color.RED.format("x", f"Fail to Download {r.status_code}")

            bar()

    mixed_ts(m3u8, folder, video_name)
    color.GREEN.format("+", f"{video_name} Download Completed")
