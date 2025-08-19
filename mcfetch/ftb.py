import requests
import json
import sqlite3
import nix
import term
import os
from running import run_parallel
from multiprocessing import Queue
from typing import Dict
from filecmp import cmp


headers: Dict
api_key: str
with open("/home/gunnar/.nixcfg/secrets/cf-api.key") as key_file:
    api_key = key_file.read().replace("\n", "")
headers = {
    "x-api-key": api_key,
    "Accept": "application/json",
}


def handle_pack(log: Queue, db: Queue, pack: int):
    global headers

    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    versions_url = f"https://api.modpacks.ch/public/modpack/{pack}"
    response = requests.get(versions_url)
    manifest = json.loads(response.content)

    if "versions" not in manifest or "updated" not in manifest:
        log.put(f"ERR: Pack {pack} manifest is invalid")
        connection.close()
        return

    # Make sure release
    if manifest["type"] != "release":
        log.put(f"Pack {pack} is beta/alpha")
        return

    # See if pack has been updated, DO NOT COMMIT
    result = cursor.execute(
        "SELECT * FROM ftb WHERE id=:id AND version='root'", {"id": pack}
    )
    rows = result.fetchall()
    if len(rows) != 0:
        row = dict(rows[0])
        if row["asset_index"] == manifest["updated"]:
            log.put(f"Pack {manifest["name"]} is up to date")
            connection.close()
            return
        else:
            row["asset_index"] = manifest["updated"]
            db.put(
                (
                    "INSERT OR REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version, :asset_index)",
                    row,
                )
            )
    else:
        db.put(
            (
                "INSERT INTO ftb VALUES(:id, 'root', null, null, null, null, :asset_index)",
                {"id": pack, "asset_index": manifest["updated"]},
            )
        )

    # Update versions
    versions = manifest["versions"]
    for version in versions:
        # Make sure is release version
        if "type" not in version or version["type"] != "release":
            continue

        # Check if version has been updated
        result = cursor.execute(
            "SELECT * FROM ftb WHERE id=:id AND version=:version",
            {"id": pack, "version": version["id"]},
        )
        rows = result.fetchall()
        if len(rows) != 0:
            row = dict(rows[0])
            if row["asset_index"] == version["updated"]:
                log.put(f"Version {version["id"]} is up to date")
                continue

        # Update version
        version_url = f"https://api.modpacks.ch/public/modpack/{pack}/{version["id"]}"
        response = requests.get(version_url)
        manifest = json.loads(response.content)

        if "files" not in manifest:
            log.put(f"ERR: {pack}:{version["id"]} missing files")
            db.put(
                (
                    "REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version, :asset_index)",
                    {
                        "id": pack,
                        "version": version["id"],
                        "filemap": None,
                        "minecraft": None,
                        "modloader": None,
                        "modloader_version": None,
                        "asset_index": "Missing Files in Manifest",
                    },
                )
            )
            continue
        if "targets" not in manifest:
            print(f"{pack}:{version["id"]} missing targets")
            db.put(
                (
                    "REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version, :asset_index)",
                    {
                        "id": pack,
                        "version": version["id"],
                        "filemap": None,
                        "minecraft": None,
                        "modloader": None,
                        "modloader_version": None,
                        "asset_index": "Missing Targets in Manifest",
                    },
                )
            )
            continue
        files = manifest["files"]
        targets = manifest["targets"]

        cur = cursor.execute(
            "SELECT * FROM ftb WHERE id=:id AND version=:version",
            {"id": pack, "version": version["id"]},
        )
        rows = cur.fetchall()

        row: Dict
        if len(rows) != 0:
            log.put(f"Updating existing verison {version["id"]}")
            row = dict(rows[0])
            row["filemap"] = json.loads(row["filemap"])
        else:
            log.put(f"Adding new version {version["id"]}")
            row = dict()
            row["id"] = pack
            row["version"] = version["id"]
            row["filemap"] = dict()

        for target in targets:
            if target["type"] == "game":
                row["minecraft"] = target["version"]
            elif target["type"] == "modloader":
                row["modloader"] = target["name"]
                row["modloader_version"] = target["version"]

        # Missing targets
        if (
            "minecraft" not in row
            or "modloader" not in row
            or "modloader_version" not in row
        ):
            log.put(f"ERR: Version {version["id"]} could not parse target in manifest")
            db.put(
                (
                    "REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version, :asset_index)",
                    {
                        "id": pack,
                        "version": version["id"],
                        "filemap": None,
                        "minecraft": None,
                        "modloader": None,
                        "modloader_version": None,
                        "asset_index": "Could Not Parse Targets From Manifest",
                    },
                )
            )
            continue

        filemap_valid = True
        filemap_reason = ""
        filemap = row["filemap"]
        for file in files:
            if term.requested:
                connection.close()
                return

            if file["clientonly"]:
                continue

            if "path" not in file or "name" not in file or "sha1" not in file:
                filemap_reason = f"Invalid File (missing required field): {file}"
                log.put(filemap_reason)
                filemap_valid = False
                break

            if "url" not in file or file["url"] == "":
                if "curseforge" in file:
                    curseforge = file["curseforge"]
                    download_url = f"https://api.curseforge.com/v1/mods/{curseforge["project"]}/files/{curseforge["file"]}/download-url"
                    response = requests.get(download_url, headers=headers)

                    if response.status_code != 200:
                        filemap_reason = (
                            f"Invalid File (download URL is NULL): {file["id"]}"
                        )
                        log.put(filemap_reason)
                        filemap_valid = False
                        break

                    else:
                        download_data = json.loads(response.content)["data"]
                        file["url"] = download_data
                else:
                    filemap_reason = (
                        f"Invalid File (no download provided): {file["id"]}"
                    )
                    log.put(filemap_reason)
                    filemap_valid = False
                    break

            if file["path"] not in filemap:
                filemap[file["path"]] = list()
            filemap[file["path"]].append(file["url"])

            cur_file = cursor.execute("SELECT * FROM files WHERE url=:url", file)
            file_rows = cur_file.fetchall()

            if len(file_rows) == 0:
                log.put(f"Adding new file {file["name"]}")
                file_row = dict()
                file_row["name"] = file["name"]
                file_row["url"] = file["url"]
                file_row["asset_index"] = file["sha1"]
                file_row["hash"] = nix.hash_native(file_row["url"], {})
                if file_row["hash"] is None:
                    filemap_reason = f"Invalid File URL: {file["id"]}"
                    log.put(filemap_reason)
                    filemap_valid = False
                    break

                db.put(
                    (
                        "INSERT INTO files VALUES(:name, :url, :asset_index, :hash)",
                        file_row,
                    )
                )

            else:
                file_row = dict(file_rows[0])
                if file_row["asset_index"] != file["sha1"]:
                    log.put(f"Updating existing file {file["name"]}")
                    file_row["url"] = file["url"]
                    file_row["hash"] = nix.hash_native(file_row["url"], {})
                    if file_row["hash"] is None:
                        filemap_reason = f"Invalid File URL: {file["id"]}"
                        log.put(filemap_reason)
                        filemap_valid = False
                        break

                    db.put(
                        (
                            "REPLACE INTO files VALUES(:name, :url, :asset_index, :hash)",
                            file_row,
                        )
                    )

        if not filemap_valid:
            db.put(
                (
                    "REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version, :asset_index)",
                    {
                        "id": pack,
                        "version": version["id"],
                        "filemap": None,
                        "minecraft": None,
                        "modloader": None,
                        "modloader_version": None,
                        "asset_index": filemap_reason,
                    },
                )
            )
            continue

        row["filemap"] = json.dumps(filemap)
        row["asset_index"] = version["updated"]

        db.put(
            (
                "REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version, :asset_index)",
                row,
            )
        )

        if term.requested:
            connection.close()
            return

    # Only commit once entire pack has been updated successfully
    log.put("Writing pack to db")
    db.put("commit")
    connection.close()


def ftb_fetch():
    url = "https://api.modpacks.ch/public/modpack/popular/installs/250"
    response = requests.get(url)
    packs = json.loads(response.content)["packs"]

    with open("cache/ftb.json", "w") as file:
        json.dump(packs, file, sort_keys=True)

    if os.path.exists("cache/ftb_old.json") and cmp(
        "cache/ftb_old.json", "cache/ftb.json"
    ):
        print("All ftb packs up to date")
        os.remove("cache/ftb.json")
        return

    packs = set(packs)
    # Remove Vanilla
    if 81 in packs:
        packs.remove(81)

    # Main Work
    run_parallel(handle_pack, packs, len(packs), "Updating ftb table in db")

    if not term.requested:
        os.replace("cache/ftb.json", "cache/ftb_old.json")
