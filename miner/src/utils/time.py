from datetime import datetime


def prettify_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return '{0}d {1:02}h {2:02}m {3:02}s'.format(int(days), int(hours), int(minutes), int(seconds))


def elapsed_time(since):
    now = datetime.now()
    elapsed = now - since
    return prettify_time(elapsed.total_seconds())
