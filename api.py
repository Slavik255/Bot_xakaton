import requests
import base64

from config import API_SERVER_URL, IMGBB_TOKEN
from data import RequestData


def get_categories():
    return requests.get(API_SERVER_URL + 'problem-categories').json()


def send_request(peer_id):
    payload = RequestData.data[peer_id]
    payload['source'] = 'Telegram'

    response = requests.post(API_SERVER_URL + 'requests', json=payload)
    return response


def get_photo_url(photo_bytes):
    photo_base64 = base64.b64encode(photo_bytes)
    
    payload = {
        'image': photo_base64.decode('ascii')
    }
    f = open('1', 'w')
    f.write(photo_base64.decode('ascii'))

    response = requests.post('https://api.imgbb.com/1/upload?key=' + IMGBB_TOKEN, payload)
    return response.json()['data']['url']