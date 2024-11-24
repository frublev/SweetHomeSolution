import logging
import os
from logging.handlers import TimedRotatingFileHandler

log_path = os.path.join(os.path.dirname(__file__), 'irrigation.log')
log_handler = TimedRotatingFileHandler(log_path, when='W6', backupCount=7)
log_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
log_handler.setFormatter(log_formatter)


def get_log(q=None):
    with open(log_path) as log_file:
        logs = log_file.readlines()
    len_log = len(logs)
    to_layout = False
    log_layout = []
    for log in reversed(logs):
        if 'INFO' in log:
            log = log.partition('INFO')
            to_layout = True
        elif 'WARNING' in log:
            log = log.partition('WARNING')
            to_layout = True
        elif 'ERROR' in log:
            log = log.partition('ERROR')
            to_layout = True
        if to_layout:
            log_time = log[0].split()
            log_time = log_time[1] + ' ' + log_time[2]
            log_layout.append({'log_time': log_time, 'log_content': log[2][:-1]})
    if q:
        log_layout = log_layout[:q]
    return log_layout


def log_for_monitor(tod_yest=None):
    logs_ = get_log()
    log_layout = []
    log_days = []
    for log in logs_:
        log_date = log['log_time'][:10]
        if not tod_yest:
            if log_date in log_days:
                log_layout.append({'log_time': log['log_time'][11:], 'log_content': log['log_content']})
            else:
                log_days.append(log_date)
                log_layout.append({'log_date': log_date})
                log_layout.append({'log_time': log['log_time'][11:], 'log_content': log['log_content']})
        else:
            if log_date in tod_yest:
                log_layout.append({'log_time': log['log_time'][11:], 'log_content': log['log_content']})
                if len(log_layout) == 0:
                    log_layout.append({'log_time': 'No logs for today and yesterday'})
    return log_layout


if __name__ == '__main__':
    print(get_log())
