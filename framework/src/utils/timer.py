import time
import math
from multiprocessing import Process, Value


def run_with_timer(target, args, timeout):
    """
    Run a function with a timeout
    :param target: a function supported by multiprocessing that returns a boolean value
    :param args: the arguments to pass to the function
    :param timeout: the timeout in seconds
    :return: a tuple of the function successfulness, its result and the time taken
    """

    # Create a shared value to store function return value
    value = Value('b', False)

    # create the list of arguments to pass to the target function
    if type(args) is tuple or type(args) is list:
        args = tuple([*args, value])
    else:
        args = (args, value)
    p = Process(target=target, args=args)

    start = time.time()
    p.start()

    p.join(timeout=timeout)
    p.terminate()
    end = time.time()

    return p.exitcode == 0, value.value == 1, math.ceil(end - start)
