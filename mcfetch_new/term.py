import signal

requested: bool = False


def exit_handler(sig, frame):
    global requested
    if not requested:
        requested = True


signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)
