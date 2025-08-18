import signal


requested: bool = False


def exit_handler(sig, frame):
    global requested

    if not requested:
        print("Wrapping up...")
    requested = True


signal.signal(signal.SIGINT, exit_handler)
