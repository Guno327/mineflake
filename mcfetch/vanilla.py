import requests
import json
import sqlite3
import nix
import term
import os
from filecmp import cmp
from rich.progress import Progress
from typing import Dict
from multiprocessing import Queue
from running import run_parallel


def fetch_jar(url: str) -> tuple[str, str] | tuple[None, None]:
    raw = requests.get(url)
    if raw.status_code != 200:
        return None, None
    json = raw.json()

    try:
        return json["downloads"]["server"]["url"], json["assetIndex"]["sha1"]
    except:
        return None, None


def handle_version(log: Queue, db: Queue, version: Dict):
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if "id" not in version:
        connection.close()
        return
    if version["type"] != "release":
        connection.close()
        return

    result = cursor.execute("SELECT * from vanilla WHERE version=:id", version)
    rows = result.fetchall()

    # New Version
    if len(rows) == 0:
        log.put(f"Adding new version {version["id"]}")

        row = dict()
        row["version"] = version["id"]
        row["url"], row["asset_index"] = fetch_jar(version["url"])
        if row["url"] is None:
            db.put(
                (
                    "INSERT INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                    {
                        "version": version["id"],
                        "url": None,
                        "asset_index": "Invalid server jar URL",
                        "hash": None,
                    },
                )
            )
            db.put("commit")
            connection.close()
            return

        row["hash"] = nix.hash_native(row["url"], {})

        db.put(
            (
                "INSERT INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                row,
            )
        )
        db.put("commit")

    # Existing Version
    else:
        # Should only ever be one row in rows
        row = dict(rows[0])

        new_url, new_asset_index = fetch_jar(version["url"])
        if new_url is None:
            db.put(
                (
                    "REPLACE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                    {
                        "version": version["id"],
                        "url": None,
                        "asset_index": "Invalid server jar URL",
                        "hash": None,
                    },
                )
            )
            db.put("commit")
            connection.close()
            return

        if new_url != row["url"] or new_asset_index != row["asset_index"]:
            log.put(f"Updating existing version {version["id"]}")
            new_hash = nix.hash_native(new_url, {})

            row["url"] = new_url
            row["asset_index"] = new_asset_index
            row["hash"] = new_hash

            db.put(
                (
                    "REPLACE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                    row,
                )
            )
            db.put("commit")
        else:
            log.put(f"Version {version["id"]} is up to date")

        connection.close()


def vanilla_fetch():
    global progress

    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    response = requests.get(manifest_url)
    manifest = json.loads(response.content)

    with open("cache/vanilla.json", "w") as file:
        json.dump(manifest, file, sort_keys=True)

    if os.path.exists("cache/vanilla_old.json") and cmp(
        "cache/vanilla_old.json", "cache/vanilla.json"
    ):
        print("All vanilla versions up to date")
        os.remove("cache/vanilla.json")
        return

    versions = manifest["versions"]

    # Main work
    run_parallel(handle_version, versions, "Updating vanilla table in db")

    # Update/Insert Latest
    if not term.requested:
        connection = sqlite3.Connection("mineflake.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        res = cursor.execute(
            "SELECT * FROM vanilla where version=:release", manifest["latest"]
        )
        rows = res.fetchall()

        if len(rows) == 0:
            print("ERR: Could not find latest version")
        else:
            row = dict(rows[0])
            row["version"] = "latest"
            cursor.execute(
                "INSERT OR REPLACE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                row,
            )
            connection.commit()
        connection.close()

    # Write results to module
    if not term.requested:
        os.replace("cache/vanilla.json", "cache/vanilla_old.json")
        nix.write_vanilla_module()
