import requests
import bs4
import re
import json
import sqlite3
from tqdm.contrib.concurrent import thread_map
import nix
from typing import Dict

script_re = re.compile(r"\<script .*?\>(.*)\</script\>")
connection: sqlite3.Connection


def handle_pack(pack: Dict):
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row

    versions = pack["versions"]
    id = pack["id"]

    for version in versions:
        cur = connection.execute(
            "SELECT * FROM ftb WHERE id=:id AND version=:version",
            {"id": id, "version": version["id"]},
        )
        rows = cur.fetchall()

        if len(rows) == 0:
            row = {}
            row["id"] = id
            row["version"] = version["id"]
            row["url"] = (
                f"https://api.feed-the-beast.com/v1/modpacks/public/modpack/{id}/{version["id"]}/server/linux"
            )
            row["asset_index"] = version["sid"]
            row["hash"] = nix.hash_url(row["url"])

            connection.execute(
                "INSERT INTO ftb VALUES(:id, :version, :url, :asset_index, :hash)", row
            )
            connection.commit()
        else:
            # Should only be one
            row = dict(rows[0])
            if row["asset_index"] != version["sid"]:
                row["asset_index"] = version["sid"]
                row["hash"] = nix.hash_url(row["url"])

                connection.execute(
                    "REPLACE INTO ftb VALUES(:id, :version, :url, :asset_index, :hash)",
                    row,
                )
                connection.commit()


def ftb_fetch():
    url = "https://www.feed-the-beast.com/modpacks?sort=release"
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.content, "html.parser")
    manifest_script = str(soup.find(id="__NEXT_DATA__"))
    manifest = script_re.split(manifest_script)
    manifest_json = json.loads(manifest[1])
    packs = manifest_json["props"]["pageProps"]["packs"]

    print(f"Updating ftb table in db: {len(packs)} packs")
    thread_map(handle_pack, packs)

    nix.write_ftb_module()
