import requests
import json
import sqlite3
import bs4
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

    if "versions" not in manifest or "updated" not in manifest:
        progress.console.log(f"ERR: Pack {manifest["name"]} is invalid")
        connection.close()
        return

    # See if pack has been updated, DO NOT COMMIT
    result = cursor.execute(
        "SELECT * FROM ftb WHERE id=:id AND version='root'", {"id": pack}
    )
    rows = result.fetchall()
    if len(rows) != 0:
        row = dict(rows[0])
        if row["asset_index"] == manifest["updated"]:
            progress.console.log(f"Pack {manifest["name"]} is up to date")
            return
        else:
            row["asset_index"] = manifest["updated"]
            cursor.execute(
                "INSERT OR REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version, :asset_index)",
                row,
            )
    else:
        cursor.execute(
            "INSERT INTO ftb VALUES(:id, 'root', null, null, null, null, :asset_index)",
            {"id": pack, "asset_index": manifest["updated"]},
        )

    # Update versions
    versions = manifest["versions"]
    version_task = progress.add_task(
        f"Updating versions for {manifest["name"]} ({pack})", total=len(versions)
    )
    for version in versions:
        # Check if version has been updated
        result = cursor.execute(
            "SELECT * FROM ftb WHERE id=:id AND version=:version",
            {"id": pack, "version": version["id"]},
        )
        rows = result.fetchall()
        if len(rows) != 0:
            row = dict(rows[0])
            if row["asset_index"] == version["updated"]:
                progress.console.log("Version is up to date")
                continue

        # Update version
        version_url = f"https://api.modpacks.ch/public/modpack/{pack}/{version["id"]}"
        response = requests.get(version_url)
        manifest = json.loads(response.content)

        if "files" not in manifest:
            progress.console.log(f"ERR: {pack}:{version["id"]} missing files")
            connection.close()
            continue
        if "targets" not in manifest:
            print(f"{pack}:{version["id"]} missing targets")
            connection.close()
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

        # Missing target, try main FTB website
        if (
            "minecraft" not in row
            or "modloader" not in row
            or "modloader_version" not in row
        ):
            progress.console.log(
                "ERR: Could not fetch targets from manifest, trying main website"
            )
            website = f"https://www.feed-the-beast.com/modpacks/{pack}"
            response = requests.get(website)
            soup = bs4.BeautifulSoup(response.content, "html.parser")
            script: str = soup.find(id="__NEXT_DATA__").string  # pyright: ignore
            script_json = json.loads(script)
            if "versions" not in script_json or "targets" not in script_json:
                progress.console.log(
                    f"ERR: Version {version["id"]} could not parse target in manifest or website"
                )
                continue

            for script_version in script_json["versions"]:
                if script_version["id"] == version["id"]:
                    progress.console.log("Found version on website")
                    for script_target in script_version["targets"]:
                        progress.console.log("Version has targets on website")
                        if script_target["type"] == "game":
                            row["minecraft"] = script_target["version"]
                        elif script_target["type"] == "modloader":
                            row["modloader"] = script_target["name"]
                            row["modloader_version"] = script_target["version"]

        # If still missing, there is nothing that can be done
        if (
            "minecraft" not in row
            or "modloader" not in row
            or "modloader_version" not in row
        ):
            progress.console.log(
                f"ERR: Version {version["id"]} could not parse target in manifest or website"
            )
            continue

        file_task = progress.add_task(
            f"Updating files for version {version["id"]}", total=len(files)
        )

        filemap_valid = True
        filemap = row["filemap"]
        for file in files:
            if file["clientonly"]:
                progress.update(file_task, advance=1)
                continue

            if "path" not in file or "name" not in file or "sha1" not in file:
                progress.console.log(
                    f"ERR: invalid file (missing required field) {file}"
                )
                filemap_valid = False
                break

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
                        f"ERR: invalid file (no url or curseforge) {file}"
                    )
                    filemap_valid = False
                    break

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
                if file_row["hash"] is None:
                    progress.console.log("ERR: File has invalid URL")
                    filemap_valid = False
                    break

                cursor.execute(
                    "INSERT INTO files VALUES(:name, :url, :asset_index, :hash)",
                    file_row,
                )

            else:
                file_row = dict(file_rows[0])
                if file_row["asset_index"] != file["sha1"]:
                    progress.console.log(f"Updating existing file {file["name"]}")
                    file_row["url"] = file["url"]
                    file_row["hash"] = nix.hash_native(
                        file_row["url"], {} if not is_curseforge else cf_heads
                    )
                    if file_row["hash"] is None:
                        progress.console.log("ERR: File has invalid URL")
                        filemap_valid = False
                        break

                    cursor.execute(
                        "REPLACE INTO files VALUES(:name, :url, :asset_index, :hash)",
                        file_row,
                    )

            progress.update(file_task, advance=1)

        progress.remove_task(file_task)
        if not filemap_valid:
            continue

        row["filemap"] = json.dumps(filemap)
        row["asset_index"] = version["updated"]

        cursor.execute(
            "INSERT OR REPLACE INTO ftb VALUES(:id, :version, :filemap, :minecraft, :modloader, :modloader_version, :asset_index)",
            row,
        )

        progress.update(version_task, advance=1)

    progress.remove_task(version_task)

    # Only commit once entire pack has been updated successfully
    progress.console.log("Writing pack to db")
    connection.commit()
    connection.close()


def ftb_fetch():
    global progress
    url = "https://api.modpacks.ch/public/modpack/popular/installs/250"
    response = requests.get(url)
    manifest = json.loads(response.content)
    packs = manifest["packs"]

    with Progress() as progress:
        progress.console.record = True
        pack_task = progress.add_task("Updating ftb table in db...", total=len(packs))
        for pack in packs:
            handle_pack(pack, progress)
            progress.update(pack_task, advance=1)

        progress.console.save_text("logs/ftb.log")
