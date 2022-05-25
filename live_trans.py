# -*- coding: utf-8 -*-

import datetime
import dateutil.parser
import json
import requests
import regex
import sys
import time
import traceback

# how to compile execution style
# pyinstaller live_trans.py --onefile

# API Key Information
JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')

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
        print('ライブはオフラインです')

    return chat_id


def get_chat(chat_id, pageToken, f_today, yt_api, deepl_API_key, cnt, DL_URL):
    # setting parameters
    url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
    params = {'key': yt_api, 'liveChatId': chat_id,'part': 'id, snippet, authorDetails'}

    if type(pageToken) == str:
        params['pageToken'] = pageToken
    else:
        print("パラメータ指定にエラーがあります")
        sys.exit()

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

        except:
            traceback.print_exc()
            f.write(traceback.print_exc())
            f.flush()
            pass

    # to get next comments
    return data['nextPageToken']


def main():
    with open('./API/key.txt', 'r') as f:
        try:
            yt_api = f.readline().replace("YouTubeAPIKey=", "").strip()
            deepl_api = f.readline().replace("DeepLAPIKey=", "").strip()
            slp_time = int(f.readline().replace("チャット取得時間間隔=", "").strip())
        except:
            print("key.txtの記述が不正です。ファイルを再確認してください。")
            sys.exit()

    while True:
        print(u'YouTubeLiveアドレスを入力してください。')
        yt_url = input()
        # checking right Live address
        if not regex.match(r'^https://www.youtube.com/watch', yt_url):
            print('正しいYouTubeアドレスを指定してください。（https://www.youtube.com/watchから始まっていますか？）')
        else:
            break

    # checking which key of DeepL API use
    # Try to use paying key
    params = {'auth_key': deepl_api, 'text': "Live streamings will help us happy!", 'target_lang': 'JA'}
    check = requests.post('https://api.deepl.com/v2/translate', data=params).json()

    if check == "<Response [403]>":
        try:
            check = requests.post('https://api-free.deepl.com/v2/translate', data=params).json()
        except:
            print("DeepL APIキーの値が正しくありません。")
            sys.exit()
        DL_URL = 'https://api-free.deepl.com/v2/translate'
    else:
        DL_URL = 'https://api.deepl.com/v2/translate'

    chat_id = get_chat_id(yt_url, yt_api)

    n_time = datetime.datetime.now()
    f_today = "Live_" + n_time.strftime('%Y-%m-%d_%H%M') + '.txt'

    nextPageToken = ''
    count = 0

    # infinity loop
    while(chat_id):
        try:
            nextPageToken = get_chat(chat_id, nextPageToken, f_today, yt_api, deepl_api, count, DL_URL)
            time.sleep(slp_time)
        except:
            break
        count += 1


if __name__ == '__main__':
    main()
