import requests
import curseforge
import nix
import sqlite3
import re
import json
from rich.progress import Progress


curse_re = re.compile(r"https://api.curseforge.com/v1/.*")

connection = sqlite3.Connection("mineflake.db")
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

result = cursor.execute("SELECT * FROM files;")
rows = result.fetchall()

with Progress() as progress:
    migrate_task = progress.add_task("Migrating entries...", total=len(rows))

    for row in rows:
        row = dict(row)
        match = curse_re.fullmatch(row["url"])
        if not match:
            progress.console.log("Not curseforge file")
            progress.update(migrate_task, advance=1)

        response = requests.get(row["url"], headers=curseforge.headers)
        try:
            file = json.loads(response.content)
            progress.console.log(file)
        except:
            continue

        exit(1)
