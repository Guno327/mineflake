import requests
import re
from zipfile import ZipFile
from io import BytesIO
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

sh_re = re.compile(r".*\.sh")


def find_script(url: str) -> str | None:
    global sh_re

    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount(url, HTTPAdapter(max_retries=retries))
        response = session.get(url, stream=True)

        if response.status_code != 200:
            return None

        zip_io = BytesIO(response.content)
    except:
        return

    with ZipFile(zip_io) as zf:
        for filename in zf.namelist():
            match = sh_re.fullmatch(filename)
            if match:
                return match[0]
    return None
