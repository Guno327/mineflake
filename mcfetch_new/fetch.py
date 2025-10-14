import util, vanilla, nix
import sqlite3

if __name__ == "__main__":
    con = sqlite3.connect(util.DB_NAME)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS vanilla(version PRIMARY KEY, url, hash, updated);
        CREATE TABLE IF NOT EXISTS ftb(id, version, files, modloader, modloader_version, minecraft_version, updated, PRIMARY KEY(id, version));
        CREATE TABLE IF NOT EXISTS cf(id, name, version, url, script, hash, updated);
    """
    )
    con.close()

    vanilla.populate()
    nix.write_vanilla_module()
