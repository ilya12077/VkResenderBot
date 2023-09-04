import html
import json
import logging
import os

import requests
from dotenv import find_dotenv, load_dotenv
from flask import Flask, request
from waitress import serve

app = Flask(__name__)

load_dotenv(find_dotenv())
url = os.environ.get('URL')
group_id_tg = os.environ.get('GROUP_ID_TG')
peer_id_vk = os.environ.get('PEER_ID_VK')
logging.info(url)
if os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False):
    path = '/etc/vkresender/'
else:
    path = ''
with open(f'{path}vknames.json', 'r') as fl:
    names = json.load(fl)
    allowed_ids_vk = list([int(id_) for id_ in names.keys()])


def send_photo_tg(chat_id: int | str, photo_url: str):
    send_body = {
        'chat_id': chat_id,
        'photo': photo_url,
        'parse_mode': 'HTML'
    }
    requests.post(url + 'sendPhoto', json=send_body)


def send_doc_tg(chat_id: int | str, doc_url: str, dop_att_flag=False):
    send_body = {
        'chat_id': chat_id,
        'document': doc_url,
        'parse_mode': 'HTML'
    }
    r = requests.post(url + 'sendDocument', json=send_body)
    if r.status_code == 400:
        print('док не отправился')
        if not dop_att_flag:
            send_message_tg(group_id_tg, '⬆️Есть доп. вложения (например опрос). Посмотрите его в вк')


def send_message_tg(chat_id: int | str, message: str, pin_message: bool = False):
    send_body = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    r = requests.post(url + 'sendMessage', json=send_body)
    if r.status_code == 400:
        send_message_tg(chat_id, html.escape(message))
    if pin_message:
        resp = json.loads(r.text)
        pin_message_tg(resp['result']['chat']['id'], resp['result']['message_id'])


def pin_message_tg(chat_id: int | str, message_id: int | str):
    send_body = {
        'chat_id': chat_id,
        'message_id': message_id
    }
    requests.post(url + 'pinChatMessage', json=send_body)


@app.route('/', methods=['GET', 'POST'])
def main():
    r = request.get_json()
    print(r)
    logging.info(r)
    if r['type'] == 'message_new':
        if r['object']['message']['peer_id'] == peer_id_vk and r['object']['message']['from_id'] in allowed_ids_vk:
            from_id = str(r['object']['message']['from_id'])
            if 'action' in r['object']['message']:
                action_type = r['object']['message']['action']['type']
                print(action_type)  # доделать
            else:
                dop_att_flag = False
                if r['object']['message']['text'] != '':
                    pin = True
                else:
                    pin = False
                send_message_tg(group_id_tg, f"{names[from_id]['name']} | {names[from_id]['role']}:\n{r['object']['message']['text']}", pin)
                if r['object']['message']['attachments']:
                    for att in r['object']['message']['attachments']:
                        if att['type'] == 'photo':
                            max_size = [0, '']
                            for count, size in enumerate(att['photo']['sizes']):
                                if size['height'] > max_size[0]:
                                    max_size = [size['height'], att['photo']['sizes'][count]['url']]
                            send_photo_tg(group_id_tg, max_size[1])
                        elif att['type'] == 'doc':
                            send_doc_tg(group_id_tg, att['doc']['url'])
                        else:
                            dop_att_flag = True
                if 'fwd_messages' in r['object']['message']:
                    if r['object']['message']['fwd_messages']:
                        dop_att_flag = True
                if 'reply_message' in r['object']['message']:
                    if r['object']['message']['reply_message']:
                        dop_att_flag = True
                if dop_att_flag:
                    send_message_tg(group_id_tg, '⬆️Есть доп. вложения (например опрос). Посмотрите его в вк')
    return 'ok'


if __name__ == '__main__':
    if os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False):
        serve(app, host='0.0.0.0', port=8882, url_scheme='http')
    else:
        app.run(host='192.168.1.10', port=8882)
