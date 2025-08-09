import requests
import json
import sqlite3
from rich.progress import Progress
import nix
from typing import Dict
from curseforge import headers as cf_heads


def handle_pack(pack: int, progress: Progress):
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    versions_url = f"https://api.modpacks.ch/public/modpack/{pack}"
    response = requests.get(versions_url)
    manifest = json.loads(response.content)

    if "versions" not in manifest:
        return

    versions = manifest["versions"]

    version_task = progress.add_task(
        f"Updating versions for {manifest["name"]} ({pack})", total=len(versions)
    )
    for version in versions:
        version_url = f"https://api.modpacks.ch/public/modpack/{pack}/{version["id"]}"
        response = requests.get(version_url)
        manifest = json.loads(response.content)

        if "files" not in manifest:
            print(f"{pack}:{version["id"]} missing files")
            return
        if "targets" not in manifest:
            print(f"{pack}:{version["id"]} missing targets")
            return
        files = manifest["files"]
        targets = manifest["targets"]

        cur = cursor.execute(
            "SELECT * FROM ftb WHERE id=:id AND version=:version",
            {"id": pack, "version": version["id"]},
        )
        rows = cur.fetchall()

        row: Dict
        if len(rows) != 0:
            progress.console.log(f"Updating existing verison {version["id"]}")
            row = dict(rows[0])
            row["filemap"] = json.loads(row["filemap"])
        else:
            progress.console.log(f"Adding new version {version["id"]}")
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

        file_task = progress.add_task(
            f"Updating files for version {version["id"]}", total=len(files)
        )

        filemap = row["filemap"]
        for file in files:
            if file["clientonly"]:
                progress.update(file_task, advance=1)
                continue

            if "path" not in file or "name" not in file or "sha1" not in file:
                progress.console.log(
                    f"ERROR: invalid file (missing required field) {file}"
                )
                connection.close()
                exit(1)

            if file["path"] not in filemap:
                filemap[file["path"]] = list()
            filemap[file["path"]].append(file["name"])

            is_curseforge = False
            if "url" not in file or file["url"] == "":
                if "curseforge" in file:
                    is_curseforge = True
                    curseforge = file["curseforge"]
                    new_url = f"https://api.curseforge.com/v1/mods/{curseforge["project"]}/files/{curseforge["file"]}"
                    file["url"] = new_url
                else:
                    progress.console.log(
                        f"ERROR: invalid file (no url or curseforge) {file}"
                    )
                    connection.close()
                    exit(1)

            cur_file = cursor.execute("SELECT * FROM files WHERE url=:url", file)
            file_rows = cur_file.fetchall()

            if len(file_rows) == 0:
                progress.console.log(f"Adding new file {file["name"]}")
                file_row = dict()
                file_row["name"] = file["name"]
                file_row["url"] = file["url"]
                file_row["asset_index"] = file["sha1"]
                file_row["hash"] = nix.hash_native(
                    file_row["url"], {} if not is_curseforge else cf_heads
                )
                cursor.execute(
                    "INSERT INTO files VALUES(:name, :url, :asset_index, :hash)",
                    file_row,
                )
                connection.commit()

            else:
                file_row = dict(file_rows[0])
                if file_row["asset_index"] != file["sha1"]:
                    progress.console.log(f"Updating existing file {file["name"]}")
                    file_row["url"] = file["url"]
                    file_row["hash"] = nix.hash_native(
                        file_row["url"], {} if not is_curseforge else cf_heads
                    )
                    cursor.execute(
                        "REPLACE INTO files VALUES(:name, :url, :asset_index, :hash)",
                        file_row,
                    )
                    connection.commit()

            progress.update(file_task, advance=1)

        progress.remove_task(file_task)

        cur = cursor.execute("SELECT COUNT(*) FROM files")
        progress.console.log(f"files db count: {cur.fetchone()[0]}")
        row["filemap"] = json.dumps(filemap)

        cursor.execute(
            "INSERT OR REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version)",
            row,
        )
        connection.commit()
        progress.update(version_task, advance=1)
    progress.remove_task(version_task)
    connection.close()


def ftb_fetch():
    global progress
    url = "https://api.modpacks.ch/public/modpack/popular/installs/250"
    response = requests.get(url)
    manifest = json.loads(response.content)
    packs = manifest["packs"]

    with Progress(transient=True) as progress:
        pack_task = progress.add_task("Updating ftb table in db...", total=len(packs))
        for pack in packs:
            handle_pack(pack, progress)
            progress.update(pack_task, advance=1)
