import requests
import sqlite3
import json
import nix
from typing import Dict

headers: Dict
api_key: str
with open("/home/gunnar/.nixcfg/secrets/cf-api.key") as key_file:
    api_key = key_file.read().replace("\n", "")
headers = {
    "x-api-key": api_key,
    "Accept": "application/json",
}
