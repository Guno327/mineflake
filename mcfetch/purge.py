import requests
import sqlite3
import json
import term
import curseforge
import running
from multiprocessing import Queue
from rich.progress import Progress
from typing import Dict


def handle_ftb_pack(log: Queue, db: Queue, row: Dict):
    if row["version"] == "root":
        return
    manifest_url = (
        f"https://api.modpacks.ch/public/modpack/{row["id"]}/{row["version"]}"
    )
    response = requests.get(manifest_url)
    release = json.loads(response.content)["type"]
    if release != "release":
        log.put(f"Removing {row["id"]}:{row["version"]}")
        db.put(
            (
                "DELETE FROM ftb WHERE id=:id AND version=:version",
                {"id": row["id"], "version": row["version"]},
            )
        )
        db.put("commit")


def handle_cf_pack(log: Queue, db: Queue, pack: Dict):
    result = cur.execute(
        "SELECT * FROM curseforge WHERE id=:slug AND url IS NOT NULL", pack
    )
    rows = result.fetchall()
    for row in rows:
        file_url = (
            f"https://api.curseforge.com/v1/mods/{pack["id"]}/files/{row["version"]}"
        )
        response = requests.get(file_url, headers=curseforge.headers)
        release = json.loads(response.content)["data"]["releaseType"]
        if release != 1:
            log.put(f"Removing {row["id"]}:{row["version"]}")
            db.put(
                (
                    "DELETE FROM curseforge WHERE id=:id AND version=:version",
                    {"id": row["id"], "version": row["version"]},
                )
            )
            db.put("commit")


conn = sqlite3.Connection("mineflake.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
result = cur.execute("SELECT * FROM ftb")
rows = result.fetchall()
packs = []
for row in rows:
    packs.append(dict(row))
running.run_parallel(
    handle_ftb_pack, packs, len(packs), "Removing non-release ftb packs"
)

all_packs = []
with Progress() as progress:
    session = requests.Session()

    fetch_task = progress.add_task("Fetching curseforge pack list", total=10000)
    for i in range(0, 9951, 50):
        if term.requested:
            break
        page: int = int(i / 50) + 1
        progress.console.log(f"Fetching page {page}")

        packs_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&classId=4471&sortField=6&sortOrder=desc&modLoaderType=1&index={i}"
        response = session.get(packs_url, headers=curseforge.headers)
        if response.status_code != 200:
            continue
        manifest_json = json.loads(response.content)
        packs = manifest_json["data"]
        all_packs = all_packs + packs
        progress.update(fetch_task, advance=50)
    progress.remove_task(fetch_task)

running.run_parallel(
    handle_cf_pack, all_packs, len(all_packs), "Removing non-release cf packs"
)
