import subprocess as sub
import sqlite3
import requests
import os
from rich.progress import Progress
from hashlib import sha256
from typing import TextIO


def hash_native(url, headers):
    try:
        # Step 1: Fetch the content
        response = requests.get(url, stream=True, headers=headers)
        if response.status_code != 200:
            return None

        with open("tmp", "wb") as file:
            file.write(response.content)

        # Step 2: Compute SHA256 hash (raw bytes)
        h = sha256()
        for chunk in response.iter_content(chunk_size=8192):
            h.update(chunk)
        digest = h.digest()  # 32-byte digest

        # Step 3: Reverse the bytes (Nix uses little-endian byte order)
        reversed_digest = digest[::-1]

        # Step 4: Nix base32 alphabet
        nix_b32_alphabet = "0123456789abcdfghijklmnpqrsvwxyz"

        # Convert bytes to big-endian integer, then to base32 using the custom alphabet
        # Pad to 160 bits (20 bytes) multiple? No — just encode the full 32 bytes
        num = int.from_bytes(reversed_digest, byteorder="big")
        if num == 0:
            return nix_b32_alphabet[0]

        encoded = ""
        while num:
            num, rem = divmod(num, 32)
            encoded = nix_b32_alphabet[rem] + encoded

        if len(encoded) > 52:
            os.error("INVALID HASH")
            exit(0)

        if len(encoded) != 52:
            encoded = "0" * (52 - len(encoded)) + encoded

        return encoded
    except:
        return None


def hash_nix(url):
    hash_raw = sub.check_output(
        ["nix-prefetch-url", "--type", "sha256", url], stderr=sub.DEVNULL
    )
    return hash_raw.decode("utf-8").rstrip()


def write_entry(file: TextIO, version: str, url: str, hash: str) -> None:
    file.write(f'"{version}"')
    file.write(" = {\n")
    file.write(f'url = "{url}";\n')
    file.write(f'sha256 = "{hash}";\n')
    file.write("};\n\n")
    return


def write_vanilla_module() -> None:
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    with open(f"../flake/sources/vanilla.nix", "w") as file:
        res = cursor.execute("SELECT * FROM vanilla WHERE url IS NOT NULL")
        rows = res.fetchall()

        with Progress() as progress:
            write_task = progress.add_task(
                "Writing vanilla packs to module...", total=len(rows)
            )
            file.write("{ ... }: {\n")
            for row in rows:
                write_entry(file, str(row["version"]), row["url"], row["hash"])
                progress.update(write_task, advance=1)
            file.write("}\n")


def write_curseforge_module() -> None:
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    with open(f"../flake/sources/curseforge.nix", "w") as file:
        res = cursor.execute("SELECT * FROM curseforge WHERE url IS NOT NULL")
        rows = res.fetchall()

        with Progress() as progress:
            progress.console.log(f"Found {len(rows)} curseforge packs")
            write_task = progress.add_task(
                "Writing curseforge packs to module", total=len(rows)
            )
            file.write("{ ... }: {\n")
            for row in rows:
                id = f"{row["id"]}:{row["version"]}"
                write_entry(file, id, row["url"], row["hash"])
                progress.update(write_task, advance=1)
            file.write("}\n")


def write_files_module() -> None:
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    with open(f"../flake/sources/curseforge.nix", "w") as file:
        res = cursor.execute("SELECT * FROM files")
        rows = res.fetchall()

        with Progress() as progress:
            write_task = progress.add_task(
                "Writing files to module...", total=len(rows)
            )

            file.write("{ ... }: {\n")
            for row in rows:
                write_entry(file, row["url"], row["url"], row["hash"])
                progress.update(write_task, advance=1)
            file.write("}\n")


def write_ftb_module() -> None:
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    with open(f"../flake/sources/curseforge.nix", "w") as file:
        res = cursor.execute("SELECT * FROM ftb WHERE filemap IS NOT NULL")
        rows = res.fetchall()

        with Progress() as progress:
            write_task = progress.add_task(
                "Writing ftb packs to module...", total=len(rows)
            )

            file.write("{ pkgs, ... }: let\n")
            file.write("files = import ./files.nix\n")
            file.write("loaders = import ./loaders.nix\n")
            file.write("in {\n")

            for row in rows:
                id = f"{row["id"]}:{row["version"]}"
                file.write(f'"{id}"')
                file.write(" = {\n")

                file.write("filemap = {\n")
                for dir in row["file_map"]:
                    file.write(f"{dir} = [\n")
                    for file in row["file_map"][dir]:
                        file.write(f'files."{file}"\n')
                    file.write("];\n")
                file.write("};\n")

                file.write(
                    f'modloader = loaders."{row["modloader"]}:{row["modloader_version"]}";\n'
                )
                file.write("};\n\n")
                progress.update(write_task, advance=1)
            file.write("}\n")
