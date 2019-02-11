import json
from os import environ
import requests
from flask import make_response

METHOD_URL = 'https://slack.com/api/channels.invite'
TOKEN: str = environ.get('TOKEN')
SUB_TOKEN: str = environ.get('SUB_TOKEN')
APP_ID: str = environ.get('APP_ID')
TEAM_ID: str = environ.get('TEAM_ID')

JSON_TYPE = 'application/json'
STATUS_REASONS = {
    400: 'Bad Request',
    403: 'Forbidden',
    405: 'Method Not Allowed',
    415: 'Unsupported Media Type',
}


def set_headers(res):
    res.headers['Content-Type'] = JSON_TYPE
    return res


def error(status: int):
    body = {
        'status': status,
        'reason': STATUS_REASONS.get(status)
    }
    res = make_response(json.dumps(body), status)
    return set_headers(res)


def invite(user: str, channel: str) -> tuple:
    payload = {
        'token': TOKEN,
        'user': user,
        'channel': channel,
        'pretty': 1
    }
    res = requests.post(METHOD_URL, params=payload)
    if JSON_TYPE not in res.headers.get('Content-Type', ''):
        return 0, {}

    return res.status_code, res.json()


def handle(event: dict) -> dict:
    if event.get('type') != 'member_left_channel':
        return {}

    user: str = event.get('user')
    channel: str = event.get('channel')
    status, result = invite(user, channel)
    res = {
        'user': user,
        'channel': channel,
        'result_status': status,
        'result_data': result
    }
    print(res)
    return res


def handler(request):
    if request.method != 'POST':
        return error(405)

    if not request.is_json or request.content_type != JSON_TYPE:
        return error(415)

    content = request.get_json()
    if content.get('token') != SUB_TOKEN:
        print('invalid subscription token:', content.get('token'))
        return error(403)

    res = {}
    if content.get('type') == 'url_verification':
        res = {'challenge': content.get('challenge')}
    elif content.get('type') == 'event_callback':
        event = content.get('event')
        if event is None or not isinstance(event, dict):
            return error(400)

        res = handle(event)
    else:
        return error(400)

    return set_headers(make_response(json.dumps(res)))
