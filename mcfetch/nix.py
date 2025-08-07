import subprocess as sub
import sqlite3
from typing import TextIO


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


def write_vanilla_module() -> None:
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row

    with open(f"../modules/vanilla.nix", "w") as file:
        res = connection.execute("SELECT * FROM vanilla")
        rows = res.fetchall()

        print(f"Writing {len(rows)} results to module vanilla.nix")
        file.write("{ pkgs, ... }: {\n")
        for row in rows:
            write_entry(file, str(row["version"]), row["url"], row["hash"])
        file.write("}\n")


def write_ftb_module() -> None:
    connection = sqlite3.Connection("mineflake.db")
    connection.row_factory = sqlite3.Row

    with open(f"../modules/ftb.nix", "w") as file:
        res = connection.execute("SELECT * FROM ftb")
        rows = res.fetchall()

        print(f"Writing {len(rows)} results to module ftb.nix")
        file.write("{pkgs, ... }: {\n")
        for row in rows:
            write_entry(
                file,
                str(row["id"]) + ":" + str(row["version"]),
                row["url"],
                row["hash"],
            )
        file.write("}\n")
