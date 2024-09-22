#!/usr/bin/python
# -*- coding: UTF-8 -*-
import asyncio
from bs4 import BeautifulSoup
from alive_progress import alive_bar
import requests, os, re, time, json, sys
# import  concurrent.futures

download_path = "{}/Anime1_Download".format(os.getcwd())
name = ""

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

async def Anime_Season(url):
    urls = []
    # https://anime1.me/category/.../...
    r = requests.post(url, headers = headers, timeout=(3,7))
    soup = BeautifulSoup(r.text, 'lxml')
    
    global name 
    name = re.search(r'(.*?) \u2013 Anime1\.me 動畫線上看', soup.find('title').text, re.M|re.I).group(1)
    if not os.path.exists(os.path.join(download_path, name)):
        os.mkdir(os.path.join(download_path, name))

    h2 = soup.find_all('h2', class_="entry-title")
    for i in h2:
        url = i.find("a", attrs={"rel": "bookmark"}).get('href')
        urls.append(url)

    # NextPage
    if(soup.find('div', class_ = 'nav-previous')):
        ele_div = soup.find('div', class_ = 'nav-previous')
        NextUrl = ele_div.find('a').get('href')
        urls.extend(await Anime_Season(NextUrl))
    urls.reverse()
    return urls

async def Anime_Episode(url):
    #1 https://anime1.me/...
    r = requests.post(url, headers = headers, timeout=(3,7))
    soup = BeautifulSoup(r.text, 'lxml') 
    data = soup.find('video', class_ = 'video-js')['data-apireq']
    title = soup.find('h2', class_="entry-title").text

    # #2 https://v.anime1.me/watch?v=...
    # r = requests.post(url,headers = headers)
    # soup = BeautifulSoup(r.text, 'lxml') 
    # script_text = soup.find_all("script")[1].string
    # xsend = 'd={}'.format(re.search(r"'d=(.*?)'", script_text, re.M|re.I).group(1))
    xsend = 'd={}'.format(data)

    #3 APIv2
    r = requests.post('https://v.anime1.me/api',headers = headers,data = xsend, timeout=(3,7))
    url = 'https:{}'.format(json.loads(r.text)['s'][0]['src'])
    
    set_cookie = r.headers['set-cookie']
    cookie_e = re.search(r"e=(.*?);", set_cookie, re.M|re.I).group(1)
    cookie_p = re.search(r"p=(.*?);", set_cookie, re.M|re.I).group(1)
    cookie_h = re.search(r"HttpOnly, h=(.*?);", set_cookie, re.M|re.I).group(1)
    cookies = 'e={};p={};h={};'.format(cookie_e, cookie_p, cookie_h)
    await MP4_DL(url, title, cookies)

async def MP4_DL(Download_URL, Video_Name, Cookies):
    # 每次下載的資料大小
    chunk_size = 10240 

    headers_cookies ={
        "accept": "*/*",
        "accept-encoding": 'identity;q=1, *;q=0',
        "accept-language": 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        "cookie": Cookies,
        "dnt": '1',
        "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    
        r = requests.get(Download_URL, headers = headers_cookies, stream=True, timeout=(3,7)) 
    # 影片大小
    content_length = int(r.headers['content-length']) 

    if(r.status_code == 200):
        print('+ \033[1;34m{}\033[0m [{size:.2f} MB]'.format(Video_Name, size = content_length / 1024 / 1024))
        # Progress Bar
        with alive_bar(round(content_length / chunk_size), spinner = 'arrows2', bar = 'filling' ) as bar:
            with open(os.path.join(download_path, name, '{}.mp4'.format(Video_Name)), 'wb') as f:
                for data in r.iter_content(chunk_size = chunk_size):
                    f.write(data)
                    f.flush()
                    bar()
            f.close()
    else:
        print("- \033[1;31mFailure\033[0m：{}".format(r.status_code)) 

async def main():

    start_time = time.time()

    if not os.path.exists(download_path):
        os.mkdir(download_path)

    anime_urls = input("? Anime1 URL：").split(',')
    
    for anime_url in anime_urls:

        url_list = []
        # 區分連結類型
        if re.search(r"anime1.me/category/(.*?)", anime_url, re.M|re.I):
            url_list.extend(await Anime_Season(anime_url))
        elif re.search(r"anime1.me/[0-9]", anime_url, re.M|re.I):
            url_list.append(anime_url)
        else:
            print("- \033[1;31mUnable to support this link. QAQ ({})\033[0m".format(anime_url))
            sys.exit(0)

        for url in url_list:
            await Anime_Episode(url)

    ## Multithreading ##
    # with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    #     executor.map(Anime_Episode, url_list)
    
    end_time = time.time()

    print(f"+ 共耗時 {round(end_time - start_time, 2)} 秒")

if __name__ == '__main__':     
    asyncio.run(main())