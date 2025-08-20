import requests
import sqlite3
import re
from running import run_parallel
from multiprocessing import Queue
from typing import Dict
from zipfile import ZipFile
from io import BytesIO


def handle_row(log: Queue, db: Queue, row: Dict):
    log.put(f"Updating pack {row["slug"]}:{row["version"]}")
    response = requests.get(row["url"])
    if response.status_code != 200:
        log.put(f"Pack {row["slug"]}:{row["version"]} has invalid download url")
        db.put(
            (
                "REPLACE INTO curseforge VALUES(:id, :version, :slug, :url, :script, :asset_index, :hash)",
                {
                    "id": row["id"],
                    "version": row["version"],
                    "slug": row["slug"],
                    "url": None,
                    "script": None,
                    "asset_index": "Download URL invalid",
                    "hash": None,
                },
            )
        )
        db.put("commit")
        return

    zip_io = BytesIO(response.content)
    with ZipFile(zip_io) as zf:
        sh_re = re.compile(r".*\.sh")
        for filename in zf.namelist():
            match = sh_re.fullmatch(filename)
            if match:
                log.put(f"Pack {row["slug"]}:{row["version"]} start script found")
                row["script"] = match[0]
                db.put(
                    (
                        "REPLACE INTO curseforge VALUES(:id, :version, :slug, :url, :script, :asset_index, :hash)",
                        row,
                    )
                )
            else:
                log.put(f"Pack {row["slug"]}:{row["version"]} has no start script")
                db.put(
                    (
                        "REPLACE INTO curseforge VALUES(:id, :version, :slug, :url, :script, :asset_index, :hash)",
                        {
                            "id": row["id"],
                            "version": row["version"],
                            "slug": row["slug"],
                            "url": None,
                            "script": None,
                            "asset_index": "No start script provided",
                            "hash": None,
                        },
                    )
                )

    db.put("commit")


connection = sqlite3.Connection("mineflake.db")
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

result = cursor.execute("SELECT * FROM curseforge WHERE url IS NOT NULL")
rows = result.fetchall()
connection.close()
rows = [dict(row) for row in rows]
run_parallel(handle_row, rows, "Updating curseforge db")
