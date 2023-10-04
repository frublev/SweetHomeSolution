from requests import get
from requests.exceptions import ConnectTimeout

url_ard = 'http://192.168.0.177/'


def request_pin_status(url):
    try:
        response_ard = get(url, timeout=20)
        if response_ard.status_code == 200:
            response_ard = response_ard.text
        else:
            response_ard = 'dddd'
    except ConnectTimeout:
        response_ard = 'dddd'
    return response_ard
