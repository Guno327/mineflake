import urllib.request as rq
import requests
import subprocess as sub
import os
import json
import sqlite3
from tqdm.contrib.concurrent import thread_map
from typing import Dict, TextIO

connection: sqlite3.Connection


def fetch_jar(url: str) -> tuple[str, str]:
    raw = requests.get(url)
    if raw.status_code != 200:
        os.error(f"FETCH FAILED: {raw.status_code}")
        exit(0)
    json = raw.json()
    return json["downloads"]["server"]["url"], json["assetIndex"]["sha1"]


def hash_url(url: str) -> str:
    hash_raw = sub.check_output(["nix-prefetch-url", url], stderr=sub.DEVNULL)
    return hash_raw.decode("utf-8").rstrip()


def write_entry(file: TextIO, version: str, url: str, hash: str) -> None:
    file.write(f'"{version}"')
    file.write(" = pkgs.fetchurl {\n")
    file.write(f'url = "{url}";\n')
    file.write(f'sha256 = "{hash}";\n')
    file.write("};\n\n")
    return


def write_module() -> None:
    global connection
    with open("../modules/vanilla.nix", "w") as file:
        res = connection.execute("SELECT * FROM vanilla")
        rows = res.fetchall()

        print(f"Writing {len(rows)} results to module vanilla.nix")
        file.write("{ pkgs, ... }: {\n")
        for row in rows:
            write_entry(file, row["version"], row["url"], row["hash"])
        file.write("}\n")
    return


def handle_version(version: Dict):
    global connection

    result = connection.execute(
        f'SELECT * from vanilla WHERE version="{version["id"]}"'
    )
    rows = result.fetchall()

    # New Version
    if len(rows) == 0:
        row = {}
        row["version"] = version["id"]
        try:
            row["url"], row["asset_index"] = fetch_jar(version["url"])
            row["hash"] = hash_url(row["url"])
        except:
            return

        connection.execute(
            "INSERT INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
            row,
        )
        connection.commit()

    # Existing Version
    else:
        # Should only ever be one row in rows
        row = rows[0]

        try:
            new_url, new_asset_index = fetch_jar(version["url"])
        except:
            return

        if new_url != row["url"] or new_asset_index != row["asset_index"]:
            try:
                new_hash = hash_url(new_url)
            except:
                return

            row["url"] = new_url
            row["asset_index"] = new_asset_index
            row["hash"] = new_hash

            connection.execute(
                "REPLACE INTO vanilla VALUES(:version, :url, :asset_index, :hash)",
                row,
            )
            connection.commit()


def vanilla_fetch(con: sqlite3.Connection):
    global connection
    connection = con
    connection.row_factory = sqlite3.Row

    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    rq.urlretrieve(manifest_url, "cache/manifest.json")
    with open("cache/manifest.json") as manifest:
        manifest_json: Dict = json.load(manifest)
        versions = manifest_json["versions"]

        print(f"Updating vanilla table in db: {len(versions)} versions")
        thread_map(handle_version, versions, dynamic_ncols=True)

    write_module()
