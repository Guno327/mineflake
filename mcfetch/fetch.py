import sqlite3
from vanilla import vanilla_fetch


con = sqlite3.connect("mineflake.db", check_same_thread=False)
con.execute(
    "CREATE TABLE IF NOT EXISTS vanilla(version PRIMARY KEY, url, asset_index, hash)"
)
vanilla_fetch(con)
con.close()
