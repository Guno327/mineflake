import requests
import sqlite3
import json
import nix
from tqdm.contrib.concurrent import thread_map
from typing import Dict

headers: Dict
api_key: str
with open("/home/gunnar/.nixcfg/secrets/cf-api.key") as key_file:
    api_key = key_file.read().replace("\n", "")
headers = {
    "x-api-key": api_key,
    "Accept": "application/json",
}


def handle_pack(pack: Dict):
    global headers

    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row

    files = pack["latestFiles"]
    latest: Dict | None = None
    for file in files:
        if (
            file["releaseType"] == 1
            and file["isAvailable"]
            and "serverPackFileId" in file
        ):
            latest = file
            break
    if latest != None:
        cur = connection.execute("SELECT * FROM curseforge WHERE id=:slug", pack)
        rows = cur.fetchall()
        if len(rows) == 0:
            row = dict()
            row["id"] = pack["slug"]
            row["asset_index"] = latest["serverPackFileId"]
            row["url"] = (
                f"https://api.curseforge.com/v1/mods/{pack["id"]}/files/{row["asset_index"]}"
            )
            row["hash"] = nix.hash_native(row["url"], headers)

            connection.execute(
                "INSERT INTO curseforge VALUES(:id, :url, :asset_index, :hash)", row
            )
            connection.commit()
        else:
            row = dict(rows[0])
            if row["asset_index"] != latest["serverPackFileId"]:
                row["asset_index"] = latest["serverPackFileId"]
                row["url"] = (
                    f"https://api.curseforge.com/v1/mods/{pack["id"]}/files/{row["asset_index"]}"
                )
                row["hash"] = nix.hash_native(row["url"], headers)

            connection.execute(
                "INSERT INTO curseforge VALUES(:id, :url, :asset_index, :hash)", row
            )
            connection.commit()
    else:
        return


def curseforge_fetch():
    global headers

    session = requests.Session()
    for i in range(0, 9951, 50):
        print(f"Updating {i}:{i+50}/10000")
        packs_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&classId=4471&sortField=6&sortOrder=desc&index={i}"
        response = session.get(packs_url, headers=headers)
        manifest_json = json.loads(response.content)
        packs = manifest_json["data"]
        thread_map(handle_pack, packs, dynamic_ncols=True)
