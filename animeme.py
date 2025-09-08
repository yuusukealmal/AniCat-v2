import os
import re
import json

import requests
from bs4 import BeautifulSoup
from alive_progress import alive_bar

import value
from value import download_path
from color import color


# 設定 Header
headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "DNT": "1",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "cookie": "__cfduid=d8db8ce8747b090ff3601ac6d9d22fb951579718376; _ga=GA1.2.1940993661.1579718377; _gid=GA1.2.1806075473.1579718377; _ga=GA1.3.1940993661.1579718377; _gid=GA1.3.1806075473.1579718377",
    "Content-Type": "application/x-www-form-urlencoded",
    "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3573.0 Safari/537.36",
}


async def Anime_Me_Season(url):
    urls = []
    # https://anime1.me/category/.../...
    r = requests.post(url, headers=headers, timeout=(3, 7))
    soup = BeautifulSoup(r.text, "lxml")

    h2 = soup.find_all("h2", class_="entry-title")
    for i in h2:
        target = i.find("a", attrs={"rel": "bookmark"}).get("href")
        urls.append(target)

    # nextPage
    if soup.find("div", class_="nav-previous"):
        ele_div = soup.find("div", class_="nav-previous")
        nextUrl = ele_div.find("a").get("href")
        urls.extend(await Anime_Me_Season(nextUrl))
    else:
        name = re.search(
            r"(.*?) \u2013 Anime1\.me 動畫線上看", soup.find("title").text, re.M | re.I
        ).group(1)
        if not os.path.exists(os.path.join(download_path, name)):
            os.mkdir(os.path.join(download_path, name))
        urls.append(name)
    return urls


async def Anime_Me_Episode(folder, url):
    r = requests.post(url, headers=headers, timeout=(3, 7))
    soup = BeautifulSoup(r.text, "lxml")
    try:
        # 1 https://anime1.me/...
        data = soup.find("video", class_="video-js")["data-apireq"]
        title = soup.find("h2", class_="entry-title").text

        # #2 https://v.anime1.me/watch?v=...
        # r = requests.post(url,headers = headers)
        # soup = BeautifulSoup(r.text, 'lxml') MP4_DL
        # script_text = soup.find_all("script")[1].string
        # xsend = 'd={}'.format(re.search(r"'d=(.*?)'", script_text, re.M|re.I).group(1))
        xsend = "d={}".format(data)

        # 3 APIv2
        r = requests.post(
            "https://v.anime1.me/api", headers=headers, data=xsend, timeout=(3, 7)
        )
        index = (
            1 if json.loads(r.text)["s"][0]["type"] == "application/x-mpegURL" else 0
        )
        url = "https:{}".format(json.loads(r.text)["s"][index]["src"])

        cookies = "".join(
            [
                f"{i}={j};"
                for i, j in re.findall(
                    r"\b([eph])=([^;,\s][^;,\s]*)", r.headers["set-cookie"]
                )
            ]
        )
        await Anime_Me_MP4_DL(url, folder, title, cookies)
    except Exception as e:
        color.RED.format(
            "x", "Error to find data for this link: {}, Cause: {}".format(url, e)
        )
        return


async def Anime_Me_MP4_DL(download_URL, folder, video_name, cookies, retries=3):
    # 每次下載的資料大小
    chunk_size = 10240

    headers_cookies = {
        "accept": "*/*",
        "accept-encoding": "identity;q=1, *;q=0",
        "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "cookie": cookies,
        "dnt": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
    }

    file_path = os.path.join(download_path, folder, f"{video_name}.mp4")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    downloaded = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    if os.path.exists(file_path) and downloaded:
        headers_cookies["Range"] = f"bytes={downloaded}-"

    try:
        r = requests.get(
            download_URL, headers=headers_cookies, stream=True, timeout=(3, 7)
        )
    except Exception as e:
        if retries > 0:
            color.YELLOW.format(
                "!", "Retry to Download:{}, Cause: {}".format(video_name, e)
            )
            return await Anime_Me_MP4_DL(
                download_URL, folder, video_name, cookies, retries - 1
            )
        else:
            color.RED.format(
                "x", "Fail to Download:{}, Cause: {}".format(video_name, e)
            )
            return None
    # 影片大小
    content_length = int(r.headers["content-length"])

    if r.status_code == 200:
        color.BLUE.format(
            "+",
            "{} [{size:.2f} MB]".format(video_name, size=content_length / 1024 / 1024),
        )
        # Progress Bar
        try:
            total_length = int(r.headers.get("content-length", 0)) + downloaded
            remaining_chunks = (total_length - downloaded) // chunk_size + 1

            color.BLUE.format(
                "+",
                f"{video_name} [{total_length / 1024 / 1024:.2f} MB] (Resume from {downloaded} bytes)",
            )

            with alive_bar(remaining_chunks, spinner="arrows2", bar="filling") as bar:
                with open(file_path, "ab") as f:
                    for data in r.iter_content(chunk_size=chunk_size):
                        f.write(data)
                        f.flush()
                        bar()

            value.eps += 1
            value.total_size += total_length - downloaded
        except Exception as e:
            color.RED.format("x", "Download Error:{}, Cause: {}".format(video_name, e))
            return await Anime_Me_MP4_DL(download_URL, folder, video_name, cookies)

    else:
        color.RED.format("x", "Fail to Download{}".format(r.status_code))
