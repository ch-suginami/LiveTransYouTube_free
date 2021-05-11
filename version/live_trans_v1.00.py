import time
from tkinter import Button, StringVar
from tkinter.constants import COMMAND
from typing import Text
import requests
import json
import sys
import re
#import tkinter as tk

YT_API_KEY = "AIzaSyCcnPvxJ9nm5vABHOAjxt0WDGUvbxefp7s"
DL_API_KEY = "5ebc8721-eb64-797d-d9bd-6e3bf637ceac"

def get_adress(event):
  return event.Button_address.get()

# translating with DeepL
def dl_trans(msg):
  params = {'auth_key': DL_API_KEY, 'text': msg, 'target_lang':'JA'}

  data = requests.post('https://api.deepl.com/v2/translate', data=params).json()

  return(data['translations'][0]['text'])

""" def drawing():
  yt_url = tk.StringVar()
  while True:
    root = tk.Tk()
    root.title('YouTubeLive 自動翻訳 with DeepL')
    root.geometry('500x500')

    main_frame = tk.Frame(root)

    Static_Input = tk.Label(main_frame, text='YouTubeLiveアドレスを入力してください')
    Entry_address = tk.Entry(main_frame, textvariable = yt_url)

    Static_test = tk.Label(text=yt_url)

    # layout
    Static_Input.pack()
    Entry_address.pack()
    Static_test.pack()

    root.mainloop()
    if not re.match(r'^https://www.youtube.com/watch',yt_url):
      print('正しいYouTubeアドレスを指定してください')
    else:
      break

  return """

def get_chat_id(yt_url):
  # getting video_id
  video_id = yt_url.replace('https://www.youtube.com/watch?v=','')
  #print(f'video_id: {video_id}')

  # requetsing
  url = 'https://www.googleapis.com/youtube/v3/videos'
  params = {'key': YT_API_KEY, 'id': video_id, 'part': 'liveStreamingDetails'}
  data = requests.get(url, params = params).json()

  # getting chat_id
  liveStreamingDetails = data['items'][0]['liveStreamingDetails']
  if 'activeLiveChatId' in liveStreamingDetails.keys():
    chat_id = liveStreamingDetails['activeLiveChatId']
    #print(chat_id)
  else:
    chat_id = None
    print('Not Active Live')

  return chat_id

def get_chat(chat_id, pageToken):
  # setting parameters
  url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
  params = {'key': YT_API_KEY, 'liveChatId': chat_id, 'part': 'id, snippet, authorDetails'}
  if type(pageToken) == str:
    params['pageToken'] = pageToken
  else:
    print("Something wrong to get params.")
    sys.exit()

  # requesting
  data = requests.get(url, params = params).json()

  #print(data)
  try:
    for item in data['items']:
      #channelId = item['snippet']['authorChannnelId']
      msg = item['snippet']['displayMessage']
      usr = item['authorDetails']['displayName']
      #supChat = item['snippet']['superChatDetails']
      #supStic = item['snippet']['superStickerDetails']
      #usr = str_left(25, usr)
      trans = dl_trans(msg)
      print(f'{usr}:')
      print(f'  original : {msg}')
      print(f'  Japanese : {trans}')
      print('')
      #print('start : {data["items"][0]["snippet"]["publishedAt"]}')
      #print('end   : {data["items"][-1]["snippet"]["publishedAt"]}')

  except:
    pass

  return data['nextPageToken']

def main(yt_url):
  slp_time = 5 # in seconds

  chat_id = get_chat_id(yt_url)

  nextPageToken = ''
  while(True):
    try:
      print('\n')
      nextPageToken = get_chat(chat_id, nextPageToken)
      time.sleep(slp_time)
    except:
      break

if __name__ == '__main__':
#  drawing()
#  sys.exit()
#  if len(sys.argv) == 2:
  while True:
    print(u'YouTubeLiveアドレスを入力してください。')
    yt_url = input()
    if not re.match(r'^https://www.youtube.com/watch',yt_url):
      print('正しいYouTubeアドレスを指定してください。（https://から始まっていますか？）')
    else:
      break
  main(yt_url)