#!/usr/bin/env python3
###########################################################
#                                                         #
#             Muti-threaded Image-Spider                  #
#                                                         #
#                   Version: 2.0                          #
#                                                         #
#                  Author: ka1n4t                         #
#                                                         #
#                Thanks to: van1997                       #
#                                                         #
#              Update-Date: 2018-02-27                    #
#                                                         #
###########################################################

from bs4 import BeautifulSoup
from urllib import request
import threading,argparse,hashlib,base64,gzip,time,os,io,re

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36',
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'zh-CN,zh;q=0.9'
    }

def md5(src):
    m = hashlib.md5()
    m.update(src.encode('utf-8'))
    return m.hexdigest()

def decode_base64(data):
    missing_padding=4-len(data)%4
    if missing_padding:
        data += '='* missing_padding
    return base64.b64decode(data)

def calculate_url(img_hash, constant):
    k = 'DECODE'
    q = 4
    constant = md5(constant)
    o = md5(constant[0:16])
    #n = md5(constant[16:16])
    n = md5(constant[16:32])
    
    l = img_hash[0:q]
    c = o+md5(o + l)

    img_hash = img_hash[q:]
    k = decode_base64(img_hash)
    h = []
    for g in range(256):
        h.append(g)

    b = []
    for g in range(256):
        b.append(ord(c[g % len(c)]))

    f = 0
    for g in range(256):
        f = (f + h[g] + b[g]) % 256
        tmp = h[g]
        h[g] = h[f]
        h[f] = tmp

    t = ""
    f = 0
    p = 0
    for g in range(len(k)):
        p = (p + 1) % 256
        f = (f + h[p]) % 256
        tmp = h[p]
        h[p] = h[f]
        h[f] = tmp
        t += chr(k[g] ^ (h[(h[p] + h[f]) % 256]))
    t = t[26:]

    return t

def get_raw_html(url):
    req = request.Request(url=url, headers=headers)
    response = request.urlopen(req)
    text = response.read()
    encoding = response.getheader('Content-Encoding')
    if encoding == 'gzip':
        buf = io.BytesIO(text)
        translated_raw = gzip.GzipFile(fileobj=buf)
        text = translated_raw.read()

    text = text.decode('utf-8')
    return text

def get_soup(html):
    soup = BeautifulSoup(html, 'lxml')
    return soup

def get_preurl(soup):
    preurl = 'http:'+soup.find(class_='previous-comment-page').get('href')
    return preurl

def get_hashesAndConstant(soup, html):
    hashes = []
    for each in soup.find_all(class_='img-hash'):
        hashes.append(each.string)

    js = re.search(r'<script\ssrc=\"\/\/(cdn.jandan.net\/static\/min\/.*?)\">.*?<\/script>', html)
    jsFileURL = 'http://'+js.group(1)
    jsFile = get_raw_html(jsFileURL)

    target_func = re.search(r'f_\w*?\(e,\"(\w*?)\"\)', jsFile)
    constant_hash = target_func.group(1)

    return hashes, constant_hash

def download_images(urls):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    for url in urls:
        filename = ''
        file_suffix = re.match(r'.*(\.\w+)', url).group(1)
        filename = md5(str(time.time()))+file_suffix
        request.urlretrieve(url, 'downloads/'+filename)
        time.sleep(3)


def spider():
    #获取url时用锁
    print(time.time())
    lock.acquire()
    global url
    html = get_raw_html(url)
    soup = get_soup(html)
    #将url替换成下一页的url，用于下一页的爬取
    url = get_preurl(soup)
    #释放锁
    lock.release()
    #get hashes&constant-hash
    params = get_hashesAndConstant(soup, html)
    hashes = params[0]
    constant_hash = params[1]
    
    urls = []
    index = 1
    for each in hashes:
        real_url = 'http:'+calculate_url(each, constant_hash)
        replace = re.match(r'(\/\/w+\.sinaimg\.cn\/)(\w+)(\/.+\.gif)', real_url)
        if replace:
            real_url = replace.group(1)+'thumb180'+replace.group(3)
        urls.append(real_url)
        index += 1

    download_images(urls)

def start(page):
    global lock
    lock = threading.Lock()
    thread_list = []
	
    #start crawling
    for i in range(page):
        t = threading.Thread(target=spider)
        thread_list.append(t)
    
    for t in thread_list:
        t.setDaemon(True)
        t.start()
    
    for t in thread_list:
        t.join()
	

if __name__ == '__main__':
    #user interface
    parser = argparse.ArgumentParser(description='download images from Jandan.net')
    parser.add_argument('-p', metavar='PAGE', default=1, type=int, help='the number of pages you want to download (default 1)')
    args = parser.parse_args()
    page = args.p

    global url
    url = 'http://jandan.net/ooxx/'

    start(page)


