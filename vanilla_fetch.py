import urllib.request as rq
import requests
import subprocess as sub
import os
import json
from tqdm import tqdm
from typing import Dict, TextIO

nix_cache: Dict = dict()


def fetch_jar(url: str) -> tuple[str, str]:
    raw = requests.get(url)
    json = raw.json()
    return json["downloads"]["server"]["url"], json["assetIndex"]["sha1"]


def hash_url(url: str) -> str:
    hash_raw = sub.check_output(["nix-prefetch-url", url], stderr=sub.DEVNULL)
    return hash_raw.decode("utf-8").rstrip()


def build_nix_cache(manifest_json: Dict) -> None:
    global nix_cache

    nix_cache["vanilla"] = dict()

    for version in tqdm(manifest_json["versions"]):
        try:
            jar, asset_index = fetch_jar(version["url"])
            hash = hash_url(jar)
        except:
            continue

        cur_dict = nix_cache["vanilla"][version["id"]] = dict()
        cur_dict["url"] = jar
        cur_dict["sha256"] = hash
        cur_dict["asset_index"] = asset_index
    nix_cache["vanilla"]["latest"] = manifest_json["latest"]["release"]

    print("Writing cache file")
    with open("cache/nix_cache.json", "w") as nix_cache_file:
        nix_cache_json = json.JSONEncoder().encode(nix_cache)
        nix_cache_file.write(nix_cache_json)


def update_nix_cache(manifest_json: Dict) -> bool:
    global nix_cache
    changed: bool = False

    if manifest_json["latest"]["release"] != nix_cache["vanilla"]["latest"]:
        changed = True
        nix_cache["vanilla"]["latests"] = manifest_json["latest"]["release"]

    for version in tqdm(manifest_json["versions"]):
        if version["id"] not in nix_cache["vanilla"]:
            try:
                jar, asset_index = fetch_jar(version["url"])
                hash = hash_url(jar)
            except:
                continue

            changed = True
            cur_dict = nix_cache["vanilla"][version["id"]] = dict()
            cur_dict["url"] = jar
            cur_dict["sha256"] = hash
            cur_dict["asset_index"] = asset_index
        else:
            try:
                jar, asset_index = fetch_jar(version["url"])
            except:
                continue

            if nix_cache["vanilla"][version["id"]]["asset_index"] != asset_index:
                try:
                    hash = hash_url(jar)
                except:
                    continue

                changed = True
                cur_dict = nix_cache["vanilla"][version["id"]] = dict()
                cur_dict["url"] = jar
                cur_dict["sha256"] = hash
                cur_dict["asset_index"] = asset_index

    if changed:
        print("Writing cache file")
        with open("cache/nix_cache.json", "w") as nix_cache_file:
            nix_cache_json = json.JSONEncoder().encode(nix_cache)
            nix_cache_file.write(nix_cache_json)
    else:
        print("No changes since last update")

    return changed


def write_entry(file: TextIO, version: str, url: str, hash: str) -> None:
    file.write(f'"{version}"')
    file.write(" = pkgs.fetchurl {\n")
    file.write(f'url = "{url}";\n')
    file.write(f'sha256 = "{hash}";\n')
    file.write("};\n\n")
    return


def write_module() -> None:
    print("Writing results to nix module")
    with open("sources/vanilla.nix", "w") as module:
        module.write("{ pkgs, ... : {\n")
        for version in nix_cache["vanilla"]:
            if version == "latest":
                write_entry(
                    module,
                    "latest",
                    nix_cache["vanilla"][nix_cache["vanilla"]["latest"]]["url"],
                    nix_cache["vanilla"][nix_cache["vanilla"]["latest"]]["hash"],
                )
            else:
                version_dict: Dict = nix_cache["vanilla"][version]
                write_entry(module, version, version_dict["url"], version_dict["hash"])
        module.write("}\n")
    return


if __name__ == "__main__":
    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    rq.urlretrieve(manifest_url, "cache/manifest.json")
    with open("cache/manifest.json") as manifest:
        manifest_json: Dict = json.load(manifest)

    update: bool = True
    if os.path.exists("cache/nix_cache.json"):
        with open("cache/nix_cache.json") as nix_cache_file:
            nix_cache: Dict = json.load(nix_cache_file)
            print("Cache exists, updating")
            update = update_nix_cache(manifest_json)
    else:
        print("Cache does not exist, building")
        build_nix_cache(manifest_json)
    if update:
        write_module()
    else:
        print("No changes to write")
