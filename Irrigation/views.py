"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, request, jsonify
from Irrigation import app
from requests import get


@app.route('/')
@app.route('/monitor')
def monitor():
    """Renders the home page."""
    return render_template(
        'monitor.html',
        title='Home Page',
        year=datetime.now().year,
    )


@app.route('/security')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )


@app.route('/irrigation', methods=['GET', 'POST'])
def irrigation():
    url_ard = 'http://192.168.0.177/'
    response = get(url_ard)
    response = response.text
    print(response)

    if request.method == 'POST':
        request_data = request.get_json()
        valve = int(request_data['valve'])
        pin = 7 - valve + 1
        print(pin)
        if response[valve-1] == 'f':
            response = get(url_ard + f'digital_pin={pin}&pin_high')
        else:
            response = get(url_ard + f'digital_pin={pin}&pin_low')
        response = response.text
        js_json = {'fn': response}
        return jsonify(js_json)

    else:
        button = []
        valve_status = []
        for i in range(3):
            if response[i] == 'f':
                print(i)
                valve_status.append('off')
                button.append('btn btn-success')
            else:
                valve_status.append('on')
                button.append('btn btn-danger')
        return render_template(
            'irrigation.html',
            title='Irrigation System',
            year=datetime.now().year,
            button1=button[0],
            valve_status1=valve_status[0],
            button2=button[1],
            valve_status2=valve_status[1],
            button3=button[2],
            valve_status3=valve_status[2],

        )
