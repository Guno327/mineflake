import requests
import sqlite3
import json
import nix
from rich.progress import Progress
from typing import Dict

headers: Dict
api_key: str
with open("/home/gunnar/.nixcfg/secrets/cf-api.key") as key_file:
    api_key = key_file.read().replace("\n", "")
headers = {
    "x-api-key": api_key,
    "Accept": "application/json",
}


def handle_pack(pack: Dict, progress: Progress):
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
            progress.console.log(f"Pack {pack["slug"]} is up to date")
            connection.close()
            return
        row["asset_index"] = pack["dateModified"]
        cursor.execute(
            "REPLACE INTO curseforge VALUES(:id, :version, :url, :asset_index, :hash)",
            row,
        )
    else:
        cursor.execute(
            "INSERT INTO curseforge VALUES(:id, :version, :url, :asset_index, :hash)",
            {
                "id": pack["slug"],
                "version": "root",
                "url": None,
                "asset_index": pack["dateModified"],
                "hash": None,
            },
        )

    files_url = f"https://api.curseforge.com/v1/mods/{pack["id"]}/files"
    response = requests.get(files_url, headers=headers)
    files = json.loads(response.content)["data"]

    file_task = progress.add_task(
        f"Updating files for {pack["slug"]}", total=len(files)
    )
    for file in files:
        if (
            "isAvailable" not in file
            or "isServerPack" not in file
            or "serverPackFileId" not in file
        ):
            progress.update(file_task, advance=1)
            continue

        if not file["isAvailable"]:
            progress.update(file_task, advance=1)
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
            progress.console.log(f"Invalid file {file["id"]}")
            progress.update(file_task, advance=1)
            continue

        result = cursor.execute(
            "SELECT * FROM curseforge WHERE id=:id AND version=:version",
            {"id": pack["slug"], "version": file["id"]},
        )
        rows = result.fetchall()

        if len(rows) != 0:
            row = dict(rows[0])
            if row["asset_index"] != file["fileFingerprint"]:
                progress.console.log(f"Updating file {file["id"]}")
                row["url"] = file["downloadUrl"]
                row["asset_index"] = file["fileFingerprint"]
                row["hash"] = nix.hash_native(row["url"], {})
                if not row["hash"]:
                    progress.console.log(f"ERR: Could not hash file {file["id"]}")
                    progress.update(file_task, advance=1)
                    continue

                cursor.execute(
                    "REPLACE INTO curseforge VALUES(:id, :version, :url, :asset_index, :hash)",
                    row,
                )
        else:
            progress.console.log(f"Adding new file {file["id"]}")
            row = dict()
            row["id"] = pack["slug"]
            row["version"] = file["id"]
            row["asset_index"] = file["fileFingerprint"]
            row["url"] = file["downloadUrl"]
            row["hash"] = nix.hash_native(row["url"], {})
            if not row["hash"]:
                progress.console.log(f"ERR: Could not hash file {file["id"]}")
                progress.update(file_task, advance=1)
                continue

            cursor.execute(
                "INSERT INTO curseforge VALUES(:id, :version, :url, :asset_index, :hash)",
                row,
            )
        progress.update(file_task, advance=1)

    progress.remove_task(file_task)
    connection.commit()
    connection.close()


def curseforge_fetch():
    global headers

    api_key: str
    with open("/home/gunnar/.nixcfg/secrets/cf-api.key") as key_file:
        api_key = key_file.read().replace("\n", "")
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
    }

    with Progress() as progress:
        table_task = progress.add_task("Updating curseforge db table...", total=10000)
        session = requests.Session()
        for i in range(0, 9951, 50):
            page_task = progress.add_task("Updating next 50 packs...", total=50)
            packs_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&classId=4471&sortField=6&sortOrder=desc&index={i}"
            response = session.get(packs_url, headers=headers)
            manifest_json = json.loads(response.content)
            packs = manifest_json["data"]
            for pack in packs:
                handle_pack(pack, progress)
                progress.update(page_task, advance=1)
            progress.remove_task(page_task)
            progress.update(table_task, completed=i + 50)
