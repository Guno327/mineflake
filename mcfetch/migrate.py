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
            progress.console.log(f"Migrating {match[2]}")
            old_url = row["url"]
            download_url = f"https://api.curseforge.com/v1/mods/{match[1]}/files/{match[2]}/download-url"
            response = requests.get(download_url, headers=curseforge.headers)
            try:
                download_data_url = json.loads(response.content)["data"]
                row["url"] = download_data_url
                row["hash"] = nix.hash_native(row["url"], {})
                cursor.execute(
                    "REPLACE INTO files VALUES(:name, :url, :asset_index, :hash)", row
                )
                connection.commit()
                progress.update(migrate_task, advance=1)
            except:
                progress.console.log(f"Deleting invalid file {match[2]}")
                cursor.execute("DELETE FROM files WHERE url=:url", {"url": old_url})
                connection.commit()
    connection.close()
