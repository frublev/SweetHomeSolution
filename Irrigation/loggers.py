import logging
import os
from logging.handlers import TimedRotatingFileHandler

log_path = os.path.join(os.path.dirname(__file__), 'irrigation.log')
log_handler = TimedRotatingFileHandler(log_path, when='W6', backupCount=7)
log_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
log_handler.setFormatter(log_formatter)


def get_log(short=False):
    with open(log_path) as log_file:
        logs = log_file.readlines()
    print(logs)
    len_log = len(logs)
    log_layout = []
    for log in reversed(logs):
        if 'INFO' in log:
            log = log.partition('INFO')
            log_time = log[0].split()
            print(log_time)
            log_time = log_time[1] + ' ' + log_time[2]
            log_layout.append({'log_time': log_time, 'log_content': log[2][:-1]})
    if short:
        log_layout = log_layout[:3]
    return log_layout


if __name__ == '__main__':
    print(get_log())
