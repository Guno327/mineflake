import sqlite3
from vanilla import vanilla_fetch
from ftb import ftb_fetch

con = sqlite3.connect("mineflake.db")
con.executescript(
    """
    CREATE TABLE IF NOT EXISTS vanilla(version PRIMARY KEY, url, asset_index, hash);
    CREATE TABLE IF NOT EXISTS ftb(id, version, filemap, minecraft, modloader, modloader_version, asset_index, PRIMARY KEY (id, version));
    CREATE TABLE IF NOT EXISTS curseforge(id PRIMARY KEY, url, asset_index, hash);
    CREATE TABLE IF NOT EXISTS files(name, url PRIMARY KEY, asset_index, hash);
    """
)
con.close()

# vanilla_fetch()
ftb_fetch()
