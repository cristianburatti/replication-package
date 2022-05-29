from datetime import datetime


def prettify_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return '{0:02}h {1:02}m {2:02}s'.format(int(hours), int(minutes), int(seconds))


def elapsed_time(since):
    now = datetime.now()
    elapsed = now - since
    return prettify_time(elapsed.total_seconds())
