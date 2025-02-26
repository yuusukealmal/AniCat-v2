#!/usr/bin/python
# -*- coding: UTF-8 -*-
import asyncio, os, re, time, sys, requests, json, math
from bs4 import BeautifulSoup
from alive_progress import alive_bar
from routes import color
# import  concurrent.futures

download_path = "{}/Anime1_Download".format(os.getcwd())
eps, total_size = 0, 0

# 設定 Header 
headers = {
    "Accept": "*/*",
    "Accept-Language": 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    "DNT": "1",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "cookie": "__cfduid=d8db8ce8747b090ff3601ac6d9d22fb951579718376; _ga=GA1.2.1940993661.1579718377; _gid=GA1.2.1806075473.1579718377; _ga=GA1.3.1940993661.1579718377; _gid=GA1.3.1806075473.1579718377",
    "Content-Type":"application/x-www-form-urlencoded",
    "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3573.0 Safari/537.36",
}

def convert_size(size):
    size_name = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    i = size//1024**(int(round(math.log(size, 1024)))-1)
    d = round(size%1024, 2)
    f = size_name[int(round(math.log(size, 1024)))-1]
    return f"{d} {f}" if i == 0 else  f"{i}.{d} {f}"

async def Anime_Season(url):
    urls = []
    # https://anime1.me/category/.../...
    r = requests.post(url, headers = headers, timeout=(3,7))
    soup = BeautifulSoup(r.text, 'lxml')

    h2 = soup.find_all('h2', class_="entry-title")
    for i in h2:
        url = i.find("a", attrs={"rel": "bookmark"}).get('href')
        urls.append(url)

    # nextPage
    if(soup.find('div', class_ = 'nav-previous')):
        ele_div = soup.find('div', class_ = 'nav-previous')
        nextUrl = ele_div.find('a').get('href')
        urls.extend(await Anime_Season(nextUrl))
    else:
        name = re.search(r'(.*?) \u2013 Anime1\.me 動畫線上看', soup.find('title').text, re.M|re.I).group(1)
        if not os.path.exists(os.path.join(download_path, name)):
            os.mkdir(os.path.join(download_path, name))
        urls.append(name)
    return urls

async def Anime_Episode(folder, url):
    r = requests.post(url, headers = headers, timeout=(3,7))
    soup = BeautifulSoup(r.text, 'lxml')
    try:
        #1 https://anime1.me/... 
        data = soup.find('video', class_ = 'video-js')['data-apireq']
        title = soup.find('h2', class_="entry-title").text

        # #2 https://v.anime1.me/watch?v=...
        # r = requests.post(url,headers = headers)
        # soup = BeautifulSoup(r.text, 'lxml') MP4_DL
        # script_text = soup.find_all("script")[1].string
        # xsend = 'd={}'.format(re.search(r"'d=(.*?)'", script_text, re.M|re.I).group(1))
        xsend = 'd={}'.format(data)

        #3 APIv2
        r = requests.post('https://v.anime1.me/api',headers = headers,data = xsend, timeout=(3,7))
        index = 1 if json.loads(r.text)['s'][0]['type'] == 'application/x-mpegURL' else 0
        url = 'https:{}'.format(json.loads(r.text)['s'][index]['src'])
        
        set_cookie = r.headers['set-cookie']
        cookie_e = re.search(r"e=(.*?);", set_cookie, re.M|re.I).group(1)
        cookie_p = re.search(r"p=(.*?);", set_cookie, re.M|re.I).group(1)
        cookie_h = re.search(r"HttpOnly, h=(.*?);", set_cookie, re.M|re.I).group(1)
        cookies = 'e={};p={};h={};'.format(cookie_e, cookie_p, cookie_h)
        await MP4_DL(url, folder, title, cookies)
    except Exception as e:
        color.RED.format("x", "Error to find data for this link: {}, Cause: {}".format(url, e))
        return

async def MP4_DL(download_URL, folder, video_name, cookies, retries=3):
    # 每次下載的資料大小
    chunk_size = 10240 
    global total_size
    global eps

    headers_cookies ={
        "accept": "*/*",
        "accept-encoding": 'identity;q=1, *;q=0',
        "accept-language": 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        "cookie": cookies,
        "dnt": '1',
        "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    
    try:
        r = requests.get(download_URL, headers=headers_cookies, stream=True, timeout=(3, 7))
    except Exception as e:
        if retries > 0:
            color.YELLOW.format("!", "Retry to Download:{}, Cause: {}".format(video_name, e))
            return await MP4_DL(download_URL, video_name, cookies, retries - 1)
        else:
            color.RED.format("x", "Fail to Download:{}, Cause: {}".format(video_name, e))
            return None
    # 影片大小
    content_length = int(r.headers['content-length'])
    file = os.path.join(download_path, folder, '{}.mp4'.format(video_name))
    
    if (os.path.exists(file) and open(os.path.join(download_path, folder, '{}.mp4'.format(video_name)), 'rb').read().__len__() == content_length):
        color.GREEN.format("-", "File Exists, Same Size as Server:{} [{}]".format(video_name, convert_size(content_length)))
        return
    if(r.status_code == 200):
        color.BLUE.format("+", "{} [{size:.2f} MB]".format(video_name, size = content_length / 1024 / 1024))
        # Progress Bar
        try:
            with alive_bar(round(content_length / chunk_size), spinner = 'arrows2', bar = 'filling' ) as bar:
                with open(os.path.join(download_path, folder, '{}.mp4'.format(video_name)), 'wb') as f:
                    for data in r.iter_content(chunk_size = chunk_size):
                        f.write(data)
                        f.flush()
                        bar()
                f.close()
            eps += 1
            total_size += content_length
        except Exception as e:
            color.RED.format("x", "Download Error:{}, Cause: {}".format(video_name, e))
            return await MP4_DL(download_URL, video_name, cookies)
    else:
        color.RED.format("x", "Fail to Download{}".format(r.status_code))

async def main():

    start_time = time.time()

    if not os.path.exists(download_path):
        os.mkdir(download_path)

    anime_urls = open('url.txt', 'r').read().splitlines()
    
    for anime_url in anime_urls:

        url_list = []
        # 區分連結類型
        if re.search(r"anime1.me/category/(.*?)", anime_url, re.M|re.I) or re.search(r"anime1.me/\?cat=[0-9]", anime_url, re.M|re.I):
            url_list.extend(await Anime_Season(anime_url))
        elif re.search(r"anime1.me/[0-9]", anime_url, re.M|re.I):
            url_list.append(anime_url)
        else:
            color.RED.format("-", "Unable to support this link. QAQ ({})".format(anime_url))
            sys.exit(0)

        folder = url_list[-1]
        url_list.pop(-1)
        for url in url_list[::-1]:
            await Anime_Episode(folder, url)

    ## Multithreading ##
    # with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    #     executor.map(Anime_Episode, url_list)
    
    end_time = time.time()

    print(f"+ 耗時 {round(end_time - start_time, 2)} 秒, 下載 {eps} 集, 總大小 {convert_size(total_size)}")

if __name__ == '__main__':     
    asyncio.run(main())