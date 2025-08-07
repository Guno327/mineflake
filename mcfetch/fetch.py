import sqlite3
from vanilla import vanilla_fetch
from curseforge import curseforge_fetch


con = sqlite3.connect("mineflake.db", check_same_thread=False)
con.execute(
    "CREATE TABLE IF NOT EXISTS vanilla(version PRIMARY KEY, url, asset_index, hash)"
)
con.execute(
    "CREATE TABLE IF NOT EXISTS ftb(id, version, url, asset_index, hash, PRIMARY KEY(id, version))"
)
con.execute(
    "CREATE TABLE IF NOT EXISTS curseforge(id PRIMARY_KEY, url, asset_index, hash)"
)
con.close()

vanilla_fetch()
# curseforge_fetch()
