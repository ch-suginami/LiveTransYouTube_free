import traceback
import locale
import time, datetime
import dateutil.parser
import requests
import json
import sys
import regex

# -*- coding: utf-8 -*-

# how to compile execution style
# pyinstaller live_trans.py --onefile

# API Key Information
YT_API_KEY_BACK_UP = "AIzaSyCcnPvxJ9nm5vABHOAjxt0WDGUvbxefp7s"
DL_API_KEY = "5ebc8721-eb64-797d-d9bd-6e3bf637ceac"
JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')

get_sleep = 3 # seconds

# translating with DeepL
def dl_trans(msg):
  params = {'auth_key': DL_API_KEY, 'text': msg, 'target_lang':'JA'}

  data = requests.post('https://api.deepl.com/v2/translate', data=params).json()

  return(data['translations'][0]['text'])


def get_chat_id(yt_url, yt_api):
  # getting video_id
  video_id = yt_url.replace('https://www.youtube.com/watch?v=','')
  #print(f'video_id: {video_id}')

  # requetsing chat ID
  url = 'https://www.googleapis.com/youtube/v3/videos'
  params = {'key': yt_api, 'id': video_id, 'part': 'liveStreamingDetails'}
  data = requests.get(url, params = params).json()

  # trying to get chat_id
  try:
    liveStreamingDetails = data['items'][0]['liveStreamingDetails']
  except:
    return False
  if 'activeLiveChatId' in liveStreamingDetails.keys():
    chat_id = liveStreamingDetails['activeLiveChatId']
    #print(chat_id)
  else:
    chat_id = None
    print('Not Active Live')

  return chat_id

def get_chat(chat_id, pageToken, f_today, yt_api, cnt):
  # setting parameters
  url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
  params = {'key': yt_api, 'liveChatId': chat_id, 'part': 'id, snippet, authorDetails'}
  if type(pageToken) == str:
    params['pageToken'] = pageToken
  else:
    print("Something wrong to get params.")
    sys.exit()

  # requesting chat itself
  data = requests.get(url, params = params).json()

  #print(data)

  with open(f_today, 'a', encoding='utf-8') as f:
    if cnt == 0 and yt_api == YT_API_KEY_BACK_UP:
      f.write(f'The API key is back up.\n')
    elif cnt == 0:
      f.write(f"The API key is streamer's.\n")
    # repeating for checking comments
    try:
      for item in data['items']:
        #channelId = item['snippet']['authorChannnelId']
        msg = item['snippet']['displayMessage']
        usr = item['authorDetails']['displayName']
        c_time = dateutil.parser.parse(item['snippet']['publishedAt']).astimezone(JST).strftime("%Y-%m-%d %H:%M:%S")
        #supStic = item['snippet']['superStickerDetails']
        #usr = str_left(25, usr)
        # checking Japanese(Hiragana or Katakana)
        if not (regex.search(r'{\p{Katakana}+}', msg) and regex.search(r'{\p{Hiragana}+}', msg)):
          # if not included, throw translation
          trans = dl_trans(msg)
        else:
          # if included, it is Japanese and not throw translation
          trans = msg
        # main output part
        # checking term 'superChat' in item list
        if item.get('superChatDetails'):
          supChatAmount = item['snippet']['superChatDetails']['amountDisplayString']
          supChatComment = item['snippet']['superChatDetails']['userComment']
          print(f'{usr}さんからスパチャが来ました！ナイスパ！！ : {usr} Thanks for superchat!')
          print(f'{supChatAmount}!')
          print(f'  original : {supChatComment}')
          print(f'  Japanese : {trans}')
          print('')
          f.write(f'{c_time}:\n{usr}:\n  金額 : {supChatAmount}\n  元コメント : {supChatComment}\n  翻訳コメント : {trans}\n\n')
          f.flush()
        else:
          print(f'{usr}:')
          print(f'  original : {msg}')
          print(f'  Japanese : {trans}')
          print('')
          f.write(f'{c_time}:\n{usr}:\n  original : {msg}\n  Japanese : {trans}\n\n')
          f.flush()

        #time.sleep(get_sleep)
        #print('start : {data["items"][0]["snippet"]["publishedAt"]}')
        #print('end   : {data["items"][-1]["snippet"]["publishedAt"]}')

    except:
      traceback.print_exc()
      f.write(traceback.print_exc())
      f.flush()
      pass

  # to get next comments
  return data['nextPageToken']

def main(yt_url, yt_api):
  slp_time = 5 # in seconds

  chat_id = get_chat_id(yt_url, yt_api)

  n_time = datetime.datetime.now()
  f_today = "Live_" + n_time.strftime('%Y-%m-%d_%H%M') + '.txt'

  nextPageToken = ''
  count = 0

  # adding counter to write API key information

  # infinity loop
  while(chat_id):
    try:
      nextPageToken = get_chat(chat_id, nextPageToken, f_today, yt_api, count)
      time.sleep(slp_time)
    except:
      break
    count += 1

  chat_id = get_chat_id(yt_url, YT_API_KEY_BACK_UP)
  count2 = 0

  while(chat_id):
    try:
      nextPageToken = get_chat(chat_id, nextPageToken, f_today, YT_API_KEY_BACK_UP, count2)
      time.sleep(slp_time)
    except Exception as e:
      print(e)
      #print('何らかの理由により、コメントの取得が終了しました。')
      print('何かキーを押してください。')
      input()
      break
    count2 += 1

if __name__ == '__main__':
  with open('./API/key.txt','r') as f:
    yt_api = f.readline()
  while True:
    print(u'YouTubeLiveアドレスを入力してください。')
    yt_url = input()
    # checking right Live address
    if not regex.match(r'^https://www.youtube.com/watch',yt_url):
      print('正しいYouTubeアドレスを指定してください。（https://www.youtube.com/watchから始まっていますか？）')
    else:
      break
  main(yt_url, yt_api)