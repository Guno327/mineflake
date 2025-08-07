import urllib.request as rq
import requests
import os
import json
import sqlite3
from threading import Lock
from tqdm.contrib.concurrent import thread_map
from typing import Dict
import nix

db_lock: Lock = Lock()


def fetch_jar(url: str) -> tuple[str, str] | tuple[None, None]:
    raw = requests.get(url)
    if raw.status_code != 200:
        os.error(f"FETCH FAILED: {raw.status_code}")
        exit(0)
    json = raw.json()

    try:
        return json["downloads"]["server"]["url"], json["assetIndex"]["sha1"]
    except:
        return None, None


def handle_version(version: Dict):
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row

    if "id" not in version:
        return

    with db_lock:
        result = connection.execute("SELECT * from vanilla WHERE version=:id", version)
        rows = result.fetchall()

    # New Version
    if len(rows) == 0:
        row = dict()
        row["version"] = version["id"]
        row["url"], row["asset_index"] = fetch_jar(version["url"])
        if row["url"] is None:
            return

        row["hash"] = nix.hash_native(row["url"], {})

        with db_lock:
            connection.execute(
                "INSERT OR IGNORE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                row,
            )
            connection.commit()

    # Existing Version
    else:
        # Should only ever be one row in rows
        row = dict(rows[0])

        new_url, new_asset_index = fetch_jar(version["url"])
        if new_url is None:
            return

        if new_url != row["url"] or new_asset_index != row["asset_index"]:
            new_hash = nix.hash_native(new_url, {})

            row["url"] = new_url
            row["asset_index"] = new_asset_index
            row["hash"] = new_hash

            with db_lock:
                connection.execute(
                    "REPLACE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                    row,
                )
                connection.commit()
    with db_lock:
        connection.close()


def vanilla_fetch():
    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    rq.urlretrieve(manifest_url, "cache/manifest.json")
    with open("cache/manifest.json") as manifest:
        manifest_json: Dict = json.load(manifest)
        versions = manifest_json["versions"]

        print(f"Updating vanilla table in db: {len(versions)} versions")
        thread_map(handle_version, versions, dynamic_ncols=True)

    nix.write_vanilla_module()
