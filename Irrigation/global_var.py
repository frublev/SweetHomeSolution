class GlobalVar:
    def __init__(self):
        self._charts = {'start': 0, 'area': [], 'durations': []}

    @property
    def charts(self):
        print('Variable requested', self._charts)
        return self._charts

    @charts.setter
    def charts(self, value):
        print('Variable changed', self._charts)
        self._charts = value


settings = GlobalVar()
