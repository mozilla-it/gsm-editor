#!/usr/bin/env python3
#
""" A script to interact with Google Secret Manager in a manner
    consistent with our usage of External Secrets Operator.

    Examples:

    # list the secret versions in the stage env
    ./gsm.py list -p moz-fx-testapp1-nonprod -e stage

    # view the latest version of the stage secret [or version 5]
    ./gsm.py view -p moz-fx-testapp1-nonprod -e stage [-v 5]

    # edit the latest version of the stage secret
    # This will create a secret for you if one does not already exist
    ./gsm.py edit -p moz-fx-testapp1-nonprod -e stage
"""

# Why am I using `subprocess` to shell out to `gcloud` instead of using the API?
# Well, it's quicker to write, for one.
# But mainly, this way doesn't require downloading and installing any additional
# python packages (like google-cloud-secret-manager) and all of its dependencies,
# which makes installing this script very much simpler.
#
# Also, I tried using the API first and got it to work once. Every time after
# that it would just time out. :(
#

import argparse
import atexit
import json
import os
import re
import subprocess
import tempfile
from hashlib import sha256


# thanks to https://www.quickprogrammingtips.com/python/how-to-calculate-sha256-hash-of-a-file-in-python.html
def shasum(filename):
    sha256_hash = sha256()
    with open(filename, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_secret(project_id, secret_id, filename):
    """
    Create a new secret with the given name. A secret is a logical wrapper
    around a collection of secret versions. Secret versions hold the actual
    secret material.
    """

    # FIXME: is an exception raised if this fails? if not, then look at return code
    result = subprocess.run(
        [
            "gcloud",
            "--project",
            project_id,
            "secrets",
            "create",
            secret_id,
            "--data-file",
            filename,
        ]
    )


def add_secret_version(project_id, secret_id, filename):
    """
    Add a new secret version to the given secret with the provided payload.
    """

    # FIXME: is an exception raised if this fails? if not, then look at return code
    result = subprocess.run(
        [
            "gcloud",
            "--project",
            project_id,
            "secrets",
            "versions",
            "add",
            secret_id,
            "--data-file",
            filename,
        ]
    )


def list_secret_versions(project_id, secret_id):
    result = subprocess.call(
        ["gcloud", "--project", project_id, "secrets", "versions", "list", secret_id]
    )


def list_secret_names(project_id, env):
    full_names = subprocess.run(
        ["gcloud", "--project", project_id, "secrets", "list", "--format=get(name)"],
        capture_output=True,
        text=True,
    )
    result = re.findall(rf"(?<={env}-gke-)(.*)(?=-secrets)", full_names.stdout)
    print("\n".join(map(str, result)))


def access_secret_version(project_id, secret_id, filename, version):
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """

    result = subprocess.run(
        [
            "gcloud",
            "--project",
            project_id,
            "secrets",
            "versions",
            "access",
            version,
            "--secret",
            secret_id,
            "--format=get(payload.data)",
        ],
        stdout=subprocess.PIPE,
    )
    if result.returncode == 1:
        # print(f"No such secret {project_id} {secret_id} {version}")
        return 0

    # to deal with possible binary data, google suggests the following transforms:
    # (see: https://cloud.google.com/sdk/gcloud/reference/secrets/versions/access)
    result_tr = subprocess.run(
        ["tr", "_-", "/+"], input=result.stdout, stdout=subprocess.PIPE
    )
    result_b64 = subprocess.run(
        ["base64", "-d"], input=result_tr.stdout, stdout=open(filename, "w", 1)
    )
    return 1


def cat_secret(project_id, secret_id, filename, version):
    with open(filename, "r") as f:
        print(f.read())


def edit_secret(filename):
    editor = os.getenv("EDITOR", "vi")

    valid_json = False

    initial_shasum = shasum(filename)

    while True:
        subprocess.call(f"{editor} {filename}", shell=True)
        # TODO: validate exit status?
        # TODO: add an option to skip validation
        try:
            json.load(open(tempfile_path))
            valid_json = True
            break
        except json.decoder.JSONDecodeError as e:
            print(e)
            again = input("Try again [Y/n]: ")
            if again != "Y" and again != "":
                break

    if not valid_json:
        raise Exception("Unable to validate JSON")

    if initial_shasum == shasum(filename):
        print("No changes. Not pushing new version")
        return 0
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "action",
        choices=["edit", "view", "list", "diff", "names"],
        help="secret action",
    )

    parser.add_argument(
        "-p", "--project", type=str, required=True, help="GCP project id"
    )

    parser.add_argument(
        "-e",
        "--env",
        type=str,
        choices=["dev", "stage", "prod"],
        required=True,
        help="secret env",
    )

    parser.add_argument(
        "-s",
        "--secret",
        type=str,
        default="app",
        required=False,
        help='custom secret identifier (default is "app")',
    )

    parser.add_argument(
        "-v",
        "--version",
        type=str,
        default="latest",
        required=False,
        help="version of the secret to create/change",
    )

    args = parser.parse_args()
    secret_name = f"{args.env}-gke-{args.secret}-secrets"

    (tempfile_fd, tempfile_path) = tempfile.mkstemp()

    # remove the tempfile on expected or unexpected program exit
    def exit_handler():
        os.unlink(tempfile_path)

    atexit.register(exit_handler)

    if args.action == "edit":
        is_existing_secret = access_secret_version(
            args.project, secret_name, tempfile_path, args.version
        )
        if edit_secret(tempfile_path):
            if is_existing_secret:
                add_secret_version(args.project, secret_name, tempfile_path)
            else:
                create_secret(args.project, secret_name, tempfile_path)
    elif args.action == "view":
        access_secret_version(args.project, secret_name, tempfile_path, args.version)
        cat_secret(args.project, secret_name, tempfile_path, args.version)
    elif args.action == "list":
        list_secret_versions(args.project, secret_name)
    elif args.action == "names":
        list_secret_names(args.project, args.env)
    elif args.action == "diff":
        print("UNIMPLEMENTED. sorry.")
