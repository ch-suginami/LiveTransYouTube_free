# -*- coding: utf-8 -*-

from distutils.util import check_environ
from faulthandler import disable
from operator import ne
from subprocess import check_output
from tkinter.messagebox import NO
import PySimpleGUI as sg

import datetime
import dateutil.parser
import json
import os
import requests
import regex
import sys
import time
import traceback

# how to compile execution style
# pyinstaller live_trans.py --onefile

# API Key Information
JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
deepl_api = "5ebc8721-eb64-797d-d9bd-6e3bf637ceac"
slp_time = 5


# translating with DeepL


def dl_trans(DL_API_KEY, URL, msg):
    params = {'auth_key': DL_API_KEY, 'text': msg, 'target_lang': 'JA'}

    data = requests.post(URL, data=params).json()

    return(data['translations'][0]['text'])


def get_chat_id(yt_url, yt_api):
    # getting video_id
    video_id = yt_url.replace('https://www.youtube.com/watch?v=', '')

    # requetsing chat ID
    url = 'https://www.googleapis.com/youtube/v3/videos'
    params = {'key': yt_api, 'id': video_id, 'part': 'liveStreamingDetails'}
    data = requests.get(url, params=params).json()

    # trying to get chat_id
    try:
        liveStreamingDetails = data['items'][0]['liveStreamingDetails']
    except:
        return False

    if 'activeLiveChatId' in liveStreamingDetails.keys():
        chat_id = liveStreamingDetails['activeLiveChatId']
    else:
        chat_id = None

    return chat_id


def get_chat(window, chat_id, pageToken, f_today, yt_api, deepl_API_key, DL_URL):
    # setting parameters
    url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
    params = {'key': yt_api, 'liveChatId': chat_id,'part': 'id, snippet, authorDetails'}

    if type(pageToken) == str:
        params['pageToken'] = pageToken
    else:
        print("パラメータ指定にエラーがあります")
        window.Refresh()

    # requesting chat itself
    data = requests.get(url, params=params).json()

    with open(f_today, 'a', encoding='utf-8') as f:
        # repeating for checking comments
        try:
            for item in data['items']:
                msg = item['snippet']['displayMessage']
                usr = item['authorDetails']['displayName']
                c_time = dateutil.parser.parse(item['snippet']['publishedAt']) \
                    .astimezone(JST).strftime("%Y-%m-%d %H:%M:%S")
                # checking Japanese(Hiragana or Katakana)
                if not (regex.search(r'{\p{Katakana}+}', msg) and regex.search(r'{\p{Hiragana}+}', msg)):
                    # if not included, throw translation
                    trans = dl_trans(deepl_API_key, DL_URL, msg)
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
                    print(f'{trans}')
                    print('')
                    window.Refresh()
                    f.write(f'{c_time}:\n{usr}:\n  金額 : {supChatAmount}\n  元コメント : {supChatComment}\n  翻訳コメント : {trans}\n\n')
                    f.flush()
                else:
                    print(f'{usr}:')
                    print(f'{trans}')
                    print('')
                    window.Refresh()
                    f.write(f'{c_time}:\n{usr}:\n  original : {msg}\n  Japanese : {trans}\n\n')
                    f.flush()

        except:
            traceback.print_exc()
            f.write(traceback.print_exc())
            f.flush()
            pass

    # to get next comments
    return data['nextPageToken']

def terminate(window):
    window.close()
    sys.exit()

def main():

    sg.theme('Dark Blue 3')

    layout = [ [sg.Text('配信URLを入力してください'), sg.InputText('', key='URL'), \
        sg.Button('コメント取得', key='translate'), sg.RealtimeButton('中止', key='stop')],
        [sg.Output(size=(95, 20))]
    ]

    window = sg.Window('YouTubeライブ翻訳ツール', layout)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            terminate(window)


        if event == 'translate':
            window['translate'].Update(disabled=True)

        # comments out only using test products
            path = './API/key.txt'.replace('/', os.sep)
            with open(path, 'r', encoding='UTF-8') as f:
                try:
                    yt_api = f.readline().replace("YouTubeAPIKey=", "").strip()
        #             deepl_api = f.readline().replace("DeepLAPIKey=", "").strip()
        #             slp_time = int(f.readline().replace("チャット取得時間間隔=", "").strip())
                except:
                    print("key.txtの記述が不正です。ファイルを再確認してください。")
                    window.Refresh()

            yt_url = values['URL']
            # checking right Live address
            if not regex.match(r'^https://www.youtube.com/watch', yt_url):
                print('正しいYouTubeアドレスを指定してください。（https://www.youtube.com/watchから始まっていますか？）')
                window.Refresh()
            else:
                pass

            # checking which key of DeepL API use
            # Try to use paying key
            params = {'auth_key': deepl_api, 'text': "Live streamings will help us happy!", 'target_lang': 'JA'}
            check = requests.post('https://api.deepl.com/v2/translate', data=params).json()

            if check == "<Response [403]>":
                try:
                    check = requests.post('https://api-free.deepl.com/v2/translate', data=params).json()
                except:
                    print("DeepL APIキーの値が正しくありません。")
                    window.Refresh()
                    sys.exit()
                DL_URL = 'https://api-free.deepl.com/v2/translate'
            else:
                DL_URL = 'https://api.deepl.com/v2/translate'

            chat_id = get_chat_id(yt_url, yt_api)

            if chat_id is None:
                print('ライブはオフラインです')
                window.Refresh()
                break

            n_time = datetime.datetime.now()
            f_today = "Live_" + n_time.strftime('%Y-%m-%d_%H%M') + '.txt'

            nextPageToken = ''

            # getting first time
            nextPageToken = get_chat(window, chat_id, nextPageToken, f_today, yt_api, deepl_api, DL_URL)

            s_point = time.time()
            # infinity loop
            while(chat_id):
                event, values = window.read(timeout=100)
                if event == sg.WIN_CLOSED:
                    terminate(window)
                elif event == 'stop':
                    print('コメント取得を終了します')
                    print("")
                    window['translate'].Update(disabled=False)
                    window.Refresh()
                    break

                # checking sleeping time
                check_time = time.time() - s_point
                if check_time > slp_time:
                    try:
                        nextPageToken = get_chat(window, chat_id, nextPageToken, f_today, yt_api, deepl_api, DL_URL)
                    except:
                        break
                    # reset time counter
                    s_point = time.time()


if __name__ == '__main__':
    main()
