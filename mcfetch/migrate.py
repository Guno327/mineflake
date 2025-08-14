import requests
import curseforge
import nix
import sqlite3
import re
import json
import signal
from rich.progress import Progress

request_exit: bool = False


def exit_handler(sig, frame):
    global request_exit
    print("Wrapping up...")
    request_exit = True


signal.signal(signal.SIGINT, exit_handler)
curse_re = re.compile(r"https://api.curseforge.com/v1/mods/(.*?)/files/(.*)")

connection = sqlite3.Connection("mineflake.db")
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

result = cursor.execute("SELECT * FROM files;")
rows = result.fetchall()

with Progress() as progress:
    migrate_task = progress.add_task("Migrating entries...", total=len(rows))

    for row in rows:
        if request_exit:
            connection.commit()
            connection.close()
            exit(1)

        row = dict(row)
        match: re.Match | None = curse_re.match(row["url"])
        if match is None:
            progress.update(migrate_task, advance=1)
        else:
            progress.console.log(f"Deleting old file {match[2]}")
            cursor.execute("DELETE FROM files WHERE url=:url", {"url": row["url"]})
            connection.commit()
            progress.update(migrate_task, advance=1)
    connection.close()
