import subprocess as sub
import sqlite3
import requests
import os
from hashlib import sha256
from typing import TextIO


def hash_native(url, headers):
    # Step 1: Fetch the content
    response = requests.get(url, stream=True, headers=headers)
    response.raise_for_status()

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


def hash_nix(url):
    hash_raw = sub.check_output(
        ["nix-prefetch-url", "--type", "sha256", url], stderr=sub.DEVNULL
    )
    return hash_raw.decode("utf-8").rstrip()


def write_entry(file: TextIO, version: str, url: str, hash: str) -> None:
    file.write(f'"{version}"')
    file.write(" = pkgs.fetchurl {\n")
    file.write(f'url = "{url}";\n')
    file.write(f'sha256 = "{hash}";\n')
    file.write("};\n\n")
    return


def write_vanilla_module() -> None:
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row

    with open(f"../sources/vanilla.nix", "w") as file:
        res = connection.execute("SELECT * FROM vanilla")
        rows = res.fetchall()

        print(f"Writing {len(rows)} results to module vanilla.nix")
        file.write("{ pkgs, ... }: {\n")
        for row in rows:
            write_entry(file, str(row["version"]), row["url"], row["hash"])
        file.write("}\n")
