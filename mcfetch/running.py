from threading import Thread
import term
import sqlite3
from functools import partial
from rich.progress import Progress
from multiprocessing import Pool, Queue, Manager
from typing import Callable, List, TypeVar, Tuple


def progress_drain(progress: Progress, logs: Queue):
    while True:
        msg = logs.get()
        if msg is None:
            return
        elif isinstance(msg, str):
            progress.console.print(msg)
        else:
            progress.console.log(str(msg))


def db_writer(db_queue: Queue):
    connection = sqlite3.Connection("mineflake.db")
    cursor = connection.cursor()
    while True:
        msg = db_queue.get()
        if msg is None:
            connection.close()
            return
        elif isinstance(msg, str):
            match str(msg):
                case "commit":
                    connection.commit()
        elif isinstance(msg, Tuple):
            command, obj = msg
            cursor.execute(command, obj)


# Main work loop
T = TypeVar("T")


def run_parallel(
    func: Callable[[Queue, Queue, T], None],
    args: List[T],
    msg: str,
):
    with Progress() as progress:
        with Manager() as manager:
            task = progress.add_task(msg, total=len(args))
            logs: Queue = manager.Queue()  # pyright: ignore
            db: Queue = manager.Queue()  # pyright: ignore
            work = partial(func, logs, db)

            log_thread = Thread(
                target=progress_drain,
                args=(
                    progress,
                    logs,
                ),
                daemon=True,
            )
            db_thread = Thread(
                target=db_writer,
                args=(db,),
                daemon=True,
            )
            log_thread.start()
            db_thread.start()

            with Pool() as pool:
                for _ in pool.imap_unordered(work, args):
                    if term.requested:
                        pool.terminate()
                        break
                    progress.update(task, advance=1)

            logs.put(None)
            db.put(None)
            log_thread.join()
            db_thread.join()
            progress.remove_task(task)
