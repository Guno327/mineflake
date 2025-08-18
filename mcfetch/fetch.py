import sqlite3
import os
from vanilla import vanilla_fetch
from ftb import ftb_fetch
from curseforge import curseforge_fetch
import term


if __name__ == "__main__":
    con = sqlite3.connect("mineflake.db")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS vanilla(version PRIMARY KEY, url, asset_index, hash);
        CREATE TABLE IF NOT EXISTS ftb(id, version, filemap, minecraft, modloader, modloader_version, asset_index, PRIMARY KEY (id, version));
        CREATE TABLE IF NOT EXISTS curseforge(id , version, url, asset_index, hash, PRIMARY KEY (id, version));
        CREATE TABLE IF NOT EXISTS files(name, url PRIMARY KEY, asset_index, hash);
        """
    )
    con.close()

    vanilla_fetch()
    if term.requested:
        if os.path.exists("tmp"):
            os.remove("tmp")
        exit(1)

    curseforge_fetch()
    if term.requested:
        if os.path.exists("tmp"):
            os.remove("tmp")
        exit(1)

    if os.path.exists("tmp"):
        os.remove("tmp")
