class GlobalVar:
    def __init__(self):
        self._charts = {'start': 0, 'area': []}

    @property
    def charts(self):
        print('Произошел запрос переменной')
        return self._charts

    @charts.setter
    def charts(self, value):
        print('Произошло изменение переменной')
        self._charts = value


settings = GlobalVar()
