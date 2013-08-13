#-*- coding:utf-8 -*-

import eyeD3
import HTMLParser
import json
import os
import threading
import threadpool
import urllib2
import urlparse

class Music:
  def __init__(self, song_id, song_name, artist_id, artist_name, album_id, album_name):
    self.song_id = song_id
    self.song_name = song_name
    self.artist_id = artist_id
    self.artist_name = artist_name
    self.album_id = album_id
    self.album_name = album_name
  
  def __str__(self):
    return 'song: ' + self.song_name + ', artist: ' + self.artist_name + ', album: ' + self.album_name
  

class Downloader:
  def __init__(self, q, base_dir='music'):
    self.current = 0
    self.total = 0
    self.q = q
    self.base_dir = base_dir
    self.lock = threading.RLock()
    self.htmlParser = HTMLParser.HTMLParser()
  

  def download_single(self, music):
    url = get_url_by_id(music.song_id)
    ext = os.path.splitext(urlparse.urlparse(url).path)[1]
    if not ext:
      print 'no file extension found, use defalut .mp3 (%s)' % url
      ext = '.mp3'
    directory = os.path.join(self.base_dir, music.artist_name, music.album_name)
    file_name = os.path.join(directory, str(music.song_name) + str(ext))
    
    self.lock.acquire()
    self.current += 1
    print '%d/%d Downloading: [ %s | %s | %s ]' % (self.current, self.total, music.song_name, music.artist_name, music.album_name)
    if os.path.exists(file_name):
      print 'Skipping exist file: %s' % music.song_name
      self.lock.release()
      return

    self.lock.release()
    resp = urllib2.urlopen(url)
    data = resp.read()

    if not os.path.exists(directory):
      os.makedirs(directory)
      
    songf = open(file_name, 'wb')
    songf.write(data)
    songf.close()
    add_tag(music, file_name)


  def download_list(self, music_list):
    pool = threadpool.ThreadPool(5)
    requests = threadpool.makeRequests(self.download_single, music_list)
    for req in requests:
        pool.putRequest(req)
    pool.wait()


  def download_all(self):
    music_results, self.total = get_search_results(self.q)
    self.download_list(music_results)
    total_page = (self.total + 7) / 8
    for page in range (2, total_page):
      music_results, self.total = get_search_results(q, page=page)
      self.download_list(music_results)

def get_search_results(q, page=1, keep_codec=False):
  q = q.replace(' ', '+')
  search_url = 'http://www.xiami.com/app/nineteen/search/key/%s/page/%d' % (q, page)
  search_url = urllib2.unquote(search_url)
  req = urllib2.Request(search_url)
  add_request_headers(req)
  resp = urllib2.urlopen(req, timeout=10)
  res_json = json.loads(resp.read())
  
  total = int(res_json['total'])
  results = res_json['results']
  music_results = []
  
  for result in results:
    music_result = Music(song_id=result['song_id'],
                         song_name=process_data_str(result['song_name'],
                                                    keep_codec=keep_codec),
                         artist_id=result['artist_id'],
                         artist_name=process_data_str(result['artist_name'],
                                                      keep_codec=keep_codec),
                         album_id=result['album_id'],
                         album_name=process_data_str(result['album_name'],
                                                     keep_codec=keep_codec))
    music_results.append(music_result)
    
  return music_results, total


def add_request_headers(req):
  #req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
  #req.add_header('Accept-Encoding', 'gzip,deflate,sdch')
  #req.add_header('Accept-Language', 'en-US,en;q=0.8')
  #req.add_header('Cache-Control', 'max-age=0')
  #req.add_header('Connection', 'keep-alive')
  #req.add_header('Cookie', '__gads=ID=61e44dbe8ecff084:T=1362677462:S=ALNI_MbXzrkkdrpbjaLtMr6V3t8WwqRI8w; __XIAMI_SESSID=30d56dae90a44215bc66d35a9e96a1e2; Hm_lvt_abe06eeb0d3656d2faeb6b2316cf22d0=1365192893; Hm_lpvt_abe06eeb0d3656d2faeb6b2316cf22d0=1366912302; base_domain_8521f0afe9404fafbd73d063dd258df0=xiami.com; 8521f0afe9404fafbd73d063dd258df0=29804a0c76e02e4c52a2ef54be2bbfcf; 8521f0afe9404fafbd73d063dd258df0_user=229459973; 8521f0afe9404fafbd73d063dd258df0_ss=a39b5736d20c13c798f84e2b6ce7cd90; 8521f0afe9404fafbd73d063dd258df0_session_key=3.c8d80d01981066060b93e7f888a9cb13.21600.1371524400-229459973; 8521f0afe9404fafbd73d063dd258df0_expires=1371524400; member_auth=026RGYhC7mtg1KDFRIoxcnBMtO3UEzbQkokDj%2BEvtAMrII5cMtevwauSQQhJ0SOqftm4zRA%2B; player_opencount=0; index_logined_hotmusic_tab=1; CNZZDATA921634=cnzz_eid%3D188696332-1362820071-http%253A%252F%252Fwww.xiami.com%26ntime%3D1371962287%26cnzz_a%3D16%26retime%3D1371962303641%26sin%3Dnone%26ltime%3D1371962303641%26rtime%3D13; __utma=251084815.717666025.1362677426.1371952516.1371962287.45; __utmc=251084815; __utmz=251084815.1371837586.42.3.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); t_sign_auth=1')
  req.add_header('Host', 'www.xiami.com')
  req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.65 Safari/537.31')
  #req.add_header('X-Forwarded-For', '220.181.111.72')
  return req


# if keep_codec is false, will use urllib2.unquote to precess.
def process_data_str(s, keep_codec=False):
  s = str(s)
  if not s:
    return s
  if not keep_codec:
    s = urllib2.unquote(s)
  return htmlParser.unescape(s).replace('+', ' ').strip()


def get_url_by_id(id):
  url = 'http://www.xiami.com/widget/json-single/sid/%s' % id
  req = urllib2.Request(url)
  add_request_headers(req)
  resp = urllib2.urlopen(req)
  res_json = json.loads(resp.read())
  location = res_json['location']
  return urllib2.unquote(decode_mp3_url(location)).replace('^', '0')


def decode_mp3_url(location):
  total_row = int(location[0])
  total_col = (len(location) + total_row - 1) / total_row
  last_col = (len(location) - 1) % total_row
  url = ''
  for index in range(0, total_col):
    for row in range(0, total_row if index < total_col - 1 else last_col):
      if index < len(location) - 1:
        url += (location[index + 1])
      index += (total_col + (0 if row < last_col else -1))
  return url


def add_tag(music, file_name):
  tag = eyeD3.Tag()
  tag.link(file_name)
  tag.setVersion(eyeD3.ID3_V2_3)
  tag.setTitle(music.song_name)  
  tag.setArtist(music.artist_name)  
  tag.setAlbum(music.album_name)
  tag.update()




if __name__ == "__main__":
  q = '陈奕迅'
  Downloader(q).download_all();
  #add_tag(Music(1,2,3,4,5,6), '/Users/hanqingliu/code/musicFinder/musicFinderApp/music/陈奕迅/Stranger Under My Skin/因为爱情.mp3');
