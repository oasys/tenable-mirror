import json
import os
from hashlib import sha256

from deb_pkg_tools.repo import update_repository
from tenable.dl import Downloads

REPO = "/var/mirror/tenable"
CONF = "~/.tenable.json"


def get_creds(file=CONF):
    with open(os.path.expanduser(file), "r") as f:
        return json.load(f)["api_token"]


def check_hash(file, match):
    if not os.path.isfile(file):
        return None
    filehash = sha256()
    with open(file, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            filehash.update(block)
    return filehash.hexdigest() == match


def valid_filename(file):
    return file.startswith("NessusAgent_") and file.endswith(".deb")


def download_new_packages(dl, dist, dir=REPO):
    packages = {
        package["file"]: package["sha256"]
        for release, releases in dl.details("nessus-agents")["releases"].items()
        if release.startswith("Nessus Agents")
        for package in releases
        if package["file"].endswith(".deb") and dist in package["file"]
    }

    files = []
    for file, sha256 in packages.items():
        name = file.replace("NessusAgent-", "NessusAgent_")
        files.append(name)
        if valid_filename(name) and not check_hash(f"{REPO}/{dist}/{name}", sha256):
            with open(f"{REPO}/{dist}/{name}", "wb") as f:
                dl.download("nessus-agents", file, f)

    return files


def remove_old_packages(packages, dir=REPO):
    for file in set(os.listdir(dir)) - set(packages):
        if valid_filename(file):
            os.remove(f"{dir}/{file}")


def main():
    for dist in ("ubuntu", "debian"):
        dir = f"{REPO}/{dist}"
        if not os.path.isdir(dir):
            os.mkdir(dir, 0o755)
        files = download_new_packages(Downloads(api_token=get_creds()), dist)
        remove_old_packages(files, dir)
        update_repository(dir)


if __name__ == "__main__":
    main()
