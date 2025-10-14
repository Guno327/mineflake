import requests
import sqlite3
import json
import nix
import term
import os
from multiprocessing import Queue
from rich.progress import Progress
from typing import Dict
from running import run_parallel
from filecmp import cmp
from util import find_script


headers: Dict
api_key: str
with open("/home/gunnar/.nixcfg/secrets/cf-api.key") as key_file:
    api_key = key_file.read().replace("\n", "")
headers = {
    "x-api-key": api_key,
    "Accept": "application/json",
}


def handle_pack(log: Queue, db: Queue, pack: Dict):
    global headers
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    connection.close()


def curseforge_fetch():
    api_key: str
    with open("/run/secrets/cf") as key_file:
        api_key = key_file.read().replace("\n", "")
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
    }

    all_packs = []
    with Progress() as progress:
        session = requests.Session()

        fetch_task = progress.add_task("Fetching curseforge pack list", total=10000)
        for i in range(0, 9951, 50):
            if term.requested:
                break
            page: int = int(i / 50) + 1
            progress.console.log(f"Fetching page {page}")

            packs_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&classId=4471&sortField=6&sortOrder=desc&index={i}"
            response = session.get(packs_url, headers=headers)
            manifest_json = json.loads(response.content)
            packs = manifest_json["data"]
            all_packs = all_packs + packs
            progress.update(fetch_task, advance=50)
        progress.remove_task(fetch_task)

    with open("cache/cf.json", "w") as file:
        json.dump(sorted(all_packs, key=lambda d: d["id"]), file)

    if os.path.exists("cache/cf_old.json") and cmp(
        "cache/cf_old.json", "cache/cf.json"
    ):
        print("All curseforge packs are up to date")
        os.remove("cache/cf.json")
        return

    run_parallel(handle_pack, all_packs, "Updating curseforge db table")
    if not term.requested:
        os.replace("cache/cf.json", "cache/cf_old.json")
        nix.write_curseforge_module()
