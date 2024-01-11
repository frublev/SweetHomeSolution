import requests


def create_unit(data_, unit):
    url_flask = 'http://192.168.0.104:5000/irrigation/' + unit + '/'
    response = requests.post(url_flask, json=data_, cookies={'token': 'bde14bfe-e862-4719-bf24-f8276ce2e59c'})
    print(response.status_code)
    print(response.json())


areas1 = {
    'head': 'Northern square',
    'description': 'North of plot',
    'square': 52.5,
}

areas2 = {
    'head': 'Southern rectangle',
    'description': 'South of plot',
    'square': 41.5,
}


areas = [areas1, areas2]

for v in areas:
    create_unit(v, 'areas')


valves1 = {
    'head': '#1',
    'description': 'Northern square',
    'model': 'Hunter PGV-100MM-B-DC',
    'jet': 16.2,
    'relay': 1,
    'area_id': 1,
}

valves2 = {
    'head': '#2',
    'description': 'Southern rectangle: West',
    'model': 'Hunter PGV-100MM-B-DC',
    'relay': 2,
    'jet': 26.1,
    'area_id': 2,
}

valves3 = {
    'head': '#3',
    'description': 'Northern square: East',
    'model': 'Hunter PGV-100MM-B-DC',
    'relay': 3,
    'jet': 25.3,
    'area_id': 2,
}

valves = [valves1, valves2, valves3]

for v in valves:
    create_unit(v, 'valves')

description = ['South West', 'North West', 'South East', 'North East',
               'West 1', 'West 2', 'West 3', 'West 4', 'West 5', 'West 6',
               'East 1', 'East 2', 'East 3', 'East 4', 'East 5']
for d in description:
    if d[0] == 'W':
        area_id = 2
        valve_id = 2
        model = 'Hunter PSU-04-10A'
    elif d[0] == 'E':
        area_id = 2
        valve_id = 3
        model = 'Hunter PSU-02-8A'
    else:
        area_id = 1
        valve_id = 1
        model = 'Gargena T100'
    if d == 'West 5' or d == 'West 6':
        sector = 90
    elif d == 'East 1':
        sector = 270
        model = 'Hunter PSU-02-10A'
    else:
        sector = 180
    sprinklers = {
        'model': model,
        'description': d,
        'sector': sector,
        'area_id': area_id,
        'valve_id': valve_id,
    }
    create_unit(sprinklers, 'sprinklers')
