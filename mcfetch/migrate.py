import requests
import sqlite3
import re
from running import run_parallel
from multiprocessing import Queue
from typing import Dict
from zipfile import ZipFile
from io import BytesIO
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def handle_row(log: Queue, db: Queue, row: Dict):
    log.put(f"Updating pack {row["slug"]}:{row["version"]}")

    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount(row["url"], HTTPAdapter(max_retries=retries))
        response = session.get(row["url"], stream=True)
    except:
        return

    if response.status_code != 200:
        db.put(
            (
                "DELETE FROM curseforge WHERE id=:id AND version=:version",
                {
                    "id": row["id"],
                    "version": row["version"],
                },
            )
        )
        db.put(
            (
                "INSERT INTO curseforge VALUES(:id, :version, :slug, :url, :script, :asset_index, :hash)",
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
    found: bool = False
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
                found = True
                break
        if not found:
            log.put(f"Pack {row["slug"]}:{row["version"]} has no start script")
            db.put(
                (
                    "DELETE FROM curseforge WHERE id=:id AND version=:version",
                    {
                        "id": row["id"],
                        "version": row["version"],
                    },
                )
            )
            db.put(
                (
                    "INSERT INTO curseforge VALUES(:id, :version, :slug, :url, :script, :asset_index, :hash)",
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

result = cursor.execute(
    "SELECT * FROM curseforge WHERE url IS NOT NULL AND script IS NULL"
)
rows = result.fetchall()
connection.close()
dict_rows = [dict(row) for row in rows]
run_parallel(handle_row, dict_rows, "Updating curseforge db")
