import timeit
import requests
from hashlib import sha256
import subprocess as sub
from functools import partial

iterations = 100


def hash_native(url):
    # Step 1: Fetch the content
    response = requests.get(url, stream=True)
    response.raise_for_status()

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

    return "0" + encoded


def hash_nix(url):
    hash_raw = sub.check_output(
        ["nix-prefetch-url", "--type", "sha256", url], stderr=sub.DEVNULL
    )
    return hash_raw.decode("utf-8").rstrip()


url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

python_hash = hash_native(url)
nix_hash = hash_nix(url)

if python_hash != nix_hash:
    print("Hashes do no match")
    print(f"NATIVE: {python_hash}")
    print(f"NIX: {nix_hash}")
    exit(0)

bounded_native = partial(hash_native, url)
bounded_nix = partial(hash_nix, url)

native_time = timeit.timeit(bounded_native, number=iterations)
nix_time = timeit.timeit(bounded_nix, number=iterations)

print(f"Native Time: {native_time}")
print(f"Nix Time: {nix_time}")
print(f"Native Speedup: {nix_time/native_time}")
