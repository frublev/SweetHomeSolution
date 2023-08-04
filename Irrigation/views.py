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
    valve_status = response.find('turned off')
    print(valve_status)

    if request.method == 'POST':
        request_data = request.get_json()
        valve = int(request_data['valve'])
        if valve_status > 1:
            response = get(url_ard + 'digital_pin=7&pin_high')
        else:
            response = get(url_ard + 'digital_pin=7&pin_low')
        response = response.text
        print(response)
        valve_status = response.find('turned off')
        if valve_status > -1:
            js_json = {
                'button_status': 'off',
                'button_class': 'btn btn-success'
            }
        else:
            js_json = {
                'button_status': 'on',
                'button_class': 'btn btn-danger'
            }
        return jsonify(js_json)

    else:
        if valve_status > -1:
            button_status = 'off'
            button = 'btn btn-success'
        else:
            button_status = 'on'
            button = 'btn btn-danger'
        print(button_status)
        return render_template(
            'irrigation.html',
            title='Irrigation System',
            year=datetime.now().year,
            button=button,
            valve_status=button_status
        )
