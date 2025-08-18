import requests
import sqlite3
import json
import nix
import term
import os
from multiprocessing import Queue
from rich.progress import Progress
from typing import Dict
from running import run_parallel
from filecmp import cmp


headers: Dict
api_key: str
with open("/home/gunnar/.nixcfg/secrets/cf-api.key") as key_file:
    api_key = key_file.read().replace("\n", "")
headers = {
    "x-api-key": api_key,
    "Accept": "application/json",
}


def handle_pack(log: Queue, db: Queue, pack: Dict):
    global headers
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    result = cursor.execute(
        "SELECT * FROM curseforge WHERE id=:id AND version=:version",
        {"id": pack["slug"], "version": "root"},
    )
    rows = result.fetchall()
    if len(rows) != 0:
        row = dict(rows[0])
        if row["asset_index"] == pack["dateModified"]:
            log.put(f"Pack {pack["slug"]} is up to date")
            connection.close()
            return
        row["asset_index"] = pack["dateModified"]
        db.put(
            (
                "REPLACE INTO curseforge VALUES(:id, :version, :url, :asset_index, :hash)",
                row,
            )
        )
    else:
        db.put(
            (
                "INSERT INTO curseforge VALUES(:id, :version, :url, :asset_index, :hash)",
                {
                    "id": pack["slug"],
                    "version": "root",
                    "url": None,
                    "asset_index": pack["dateModified"],
                    "hash": None,
                },
            )
        )

    files_url = f"https://api.curseforge.com/v1/mods/{pack["id"]}/files"
    response = requests.get(files_url, headers=headers)
    files = json.loads(response.content)["data"]

    for file in files:
        if (
            "isAvailable" not in file
            or "isServerPack" not in file
            or "serverPackFileId" not in file
        ):
            continue

        if not file["isAvailable"]:
            continue

        if not file["isServerPack"]:
            server_url = f"https://api.curseforge.com/v1/mods/{pack["id"]}/files/{file["serverPackFileId"]}"
            response = requests.get(server_url, headers=headers)
            new_file = json.loads(response.content)["data"]
            file = new_file

        if (
            "id" not in file
            or "downloadUrl" not in file
            or "fileFingerprint" not in file
        ):
            log.put(f"Invalid file {file["id"]}")
            continue

        result = cursor.execute(
            "SELECT * FROM curseforge WHERE id=:id AND version=:version",
            {"id": pack["slug"], "version": file["id"]},
        )
        rows = result.fetchall()

        if len(rows) != 0:
            row = dict(rows[0])
            if row["asset_index"] != file["fileFingerprint"]:
                log.put(f"{pack["slug"]}: Updating file {file["id"]}")
                row["url"] = file["downloadUrl"]
                row["asset_index"] = file["fileFingerprint"]
                row["hash"] = nix.hash_native(row["url"], {})
                if not row["hash"]:
                    log.put(f"ERR: Could not hash file {file["id"]}")
                    continue

                db.put(
                    (
                        "REPLACE INTO curseforge VALUES(:id, :version, :url, :asset_index, :hash)",
                        row,
                    )
                )
        else:
            log.put(f"{pack["slug"]}: Adding new file {file["id"]}")
            row = dict()
            row["id"] = pack["slug"]
            row["version"] = file["id"]
            row["asset_index"] = file["fileFingerprint"]
            row["url"] = file["downloadUrl"]
            row["hash"] = nix.hash_native(row["url"], {})
            if not row["hash"]:
                log.put(f"ERR: Could not hash file {file["id"]}")
                continue

            db.put(
                (
                    "INSERT INTO curseforge VALUES(:id, :version, :url, :asset_index, :hash)",
                    row,
                )
            )

    log.put(f"Finished updating pack {pack["slug"]}")
    db.put("commit")
    connection.close()


def curseforge_fetch():
    api_key: str
    with open("/home/gunnar/.nixcfg/secrets/cf-api.key") as key_file:
        api_key = key_file.read().replace("\n", "")
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
    }

    all_packs = []
    with Progress() as progress:
        session = requests.Session()

        fetch_task = progress.add_task("Fetching curseforge pack list", total=10000)
        for i in range(0, 9951, 50):
            if term.requested:
                break
            page: int = int(i / 50) + 1
            progress.console.log(f"Fetching page {page}")

            packs_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&classId=4471&sortField=6&sortOrder=desc&index={i}"
            response = session.get(packs_url, headers=headers)
            manifest_json = json.loads(response.content)
            packs = manifest_json["data"]
            all_packs = all_packs + packs
            progress.update(fetch_task, advance=50)
        progress.remove_task(fetch_task)

    with open("cache/cf.json", "w") as file:
        json.dump(sorted(all_packs, key=lambda d: d["id"]), file)

    if os.path.exists("cache/cf_old.json") and cmp(
        "cache/cf_old.json", "cache/cf.json"
    ):
        print("All curseforge packs are up to date")
        os.remove("cache/cf.json")
        return

    run_parallel(handle_pack, all_packs, len(all_packs), "Updating curseforge db table")
    if not term.requested:
        os.replace("cache/cf.json", "cache/cf_old.json")
        nix.write_curseforge_module()
