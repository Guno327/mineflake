import util, nix, term
from rich.progress import Progress
from typing import Dict

MANIFEST_URL: str = "https://launchermeta.mojang.com/mc/game/version_manifest.json"


def update_version(version: Dict, p: Progress) -> None:
    if version["type"] != "release":
        return

    # Get version JAR
    if not (manifest := util.fetch_json(version["url"])):
        p.console.log(
            f"Could not update version {version["id"]} (could not fetch version manifest)"
        )
        return

    # Get db row
    row = util.db_fetchone("SELECT * FROM vanilla WHERE version=:id", version)

    # Update row
    if not row or row["updated"] != manifest["assetIndex"]["sha1"]:
        p.console.log(f"Updating version {version["id"]}")

        row = dict()
        row["version"] = version["id"]
        row["url"] = manifest["downloads"]["server"]["url"]
        row["updated"] = manifest["assetIndex"]["sha1"]
        row["hash"] = nix.hash_native(row["url"])

        if not row["hash"]:
            p.console.log(
                f"Could not update version {version["id"]} (could not hash server jar)"
            )
            return

        util.db_execute(
            "REPLACE INTO vanilla VALUES(:version, :url, :hash, :updated)", row
        )
    else:
        p.console.log(f"Version {version["id"]} is up to date")

    return


def populate():
    # Get manifest
    if not (manifest := util.fetch_json(MANIFEST_URL)):
        print(
            f"Could not get vanilla version manifest (could not get versions manifest)"
        )
        return

    with Progress() as p:
        version_task = p.add_task(
            "Updating vanilla db table", total=len(manifest["versions"])
        )

        # Update versions
        for version in manifest["versions"]:
            if term.requested:
                p.console.log("Exiting early")
                break
            try:
                update_version(version, p)
            except KeyError:
                p.console.log(
                    f"Could not update version {version["id"]} (malformed version manifest)"
                )
            p.advance(version_task, advance=1)
        p.remove_task(version_task)

    return
