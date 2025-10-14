import sqlite3
import requests
import json
from typing import Dict, Optional

DB_NAME: str = "mineflake.db"


def fetch_json(url: str, headers: Dict = {}) -> Optional[Dict]:
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return

    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return


def db_fetchone(cmd: str, vars: Dict) -> Optional[Dict]:
    con = sqlite3.connect(DB_NAME)
    con.row_factory = sqlite3.Row
    cur = con.execute(cmd, vars)
    row = cur.fetchone()
    con.close()
    return row


def db_fetchall(cmd: str, vars: Dict) -> Optional[list[Dict]]:
    con = sqlite3.connect(DB_NAME)
    con.row_factory = sqlite3.Row
    cur = con.execute(cmd, vars)
    rows = cur.fetchall()
    con.close()
    return rows


def db_execute(cmd: str, vars: Dict) -> None:
    con = sqlite3.connect(DB_NAME)
    con.execute(cmd, vars)
    con.commit()
    con.close()
    return
