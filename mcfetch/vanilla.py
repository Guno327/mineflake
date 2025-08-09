import urllib.request as rq
import requests
import os
import json
import sqlite3
from rich.progress import Progress
from typing import Dict
import nix


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


def handle_version(version: Dict, progress: Progress):
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if "id" not in version:
        return

    result = cursor.execute("SELECT * from vanilla WHERE version=:id", version)
    rows = result.fetchall()

    # New Version
    if len(rows) == 0:
        progress.console.log(f"Adding new version {version["id"]}")

        row = dict()
        row["version"] = version["id"]
        row["url"], row["asset_index"] = fetch_jar(version["url"])
        if row["url"] is None:
            return

        row["hash"] = nix.hash_native(row["url"], {})

        cursor.execute(
            "INSERT OR IGNORE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
            row,
        )
        connection.commit()

    # Existing Version
    else:
        progress.console.log(f"Updating existing version {version["id"]}")
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

            cursor.execute(
                "REPLACE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                row,
            )
            connection.commit()
        connection.close()


def vanilla_fetch():
    global progress

    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    rq.urlretrieve(manifest_url, "cache/manifest.json")
    with open("cache/manifest.json") as manifest:
        manifest_json: Dict = json.load(manifest)
        versions = manifest_json["versions"]

        with Progress() as p:
            progress = p
            version_task = progress.add_task(
                "Updating vanilla table in db...", total=len(versions)
            )

            for version in versions:
                handle_version(version, progress)
                progress.update(version_task, advance=1)

        # Update/Insert Latest
        connection = sqlite3.Connection("mineflake.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        res = cursor.execute(
            "SELECT * FROM vanilla where version=:release", manifest_json["latest"]
        )
        rows = res.fetchall()

        if len(rows) == 0:
            print("Could not find latest version")
            exit(0)
        else:
            row = dict(rows[0])
            row["version"] = "latest"
            cursor.execute(
                "INSERT OR REPLACE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                row,
            )
            connection.commit()
        connection.close()

    nix.write_vanilla_module()
