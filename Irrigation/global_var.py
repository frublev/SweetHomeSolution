class GlobalVar:
    def __init__(self):
        self._charts = {'start': 0, 'area': [], 'durations': [], 'alert': []}

    @property
    def charts(self):
        print('Variable requested', self._charts)
        return self._charts

    @charts.setter
    def charts(self, value):
        print('Variable changed', self._charts)
        self._charts = value


settings = GlobalVar()

alerts_type = [
    {
        'head': 'Connect error',
        'description': 'No connection to valves'
    }
]
