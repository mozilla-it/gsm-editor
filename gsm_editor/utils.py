import json
import os
import subprocess
from hashlib import sha256

import pathlib

from gsm_editor.exceptions import SecretNotFoundError
from gsm_editor.models import Secret


# thanks to https://www.quickprogrammingtips.com/python/how-to-calculate-sha256-hash-of-a-file-in-python.html
def shasum(file: pathlib.Path):
    sha256_hash = sha256()
    with open(file, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_secret(secret: Secret, file: pathlib.Path):
    """
    Create a new secret with the given name. A secret is a logical wrapper
    around a collection of secret versions. Secret versions hold the actual
    secret material.
    """

    # FIXME: is an exception raised if this fails? if not, then look at return code
    subprocess.run(
        [
            "gcloud",
            "--project",
            secret.project_id,
            "secrets",
            "create",
            secret.secret_name,
            "--data-file",
            file,
        ]
    )


def add_secret_version(secret: Secret, file: pathlib.Path):
    """
    Add a new secret version to the given secret with the provided payload.
    """

    # FIXME: is an exception raised if this fails? if not, then look at return code
    subprocess.run(
        [
            "gcloud",
            "--project",
            secret.project_id,
            "secrets",
            "versions",
            "add",
            secret.secret_name,
            "--data-file",
            file,
        ]
    )


def get_secret_version(secret: Secret) -> str:
    """
    Get secret version content and return UTF8 encoded string
    """

    result = subprocess.run(
        [
            "gcloud",
            "--project",
            secret.project_id,
            "secrets",
            "versions",
            "access",
            secret.version,
            "--secret",
            secret.secret_name,
            "--format=get(payload.data)",
        ],
        stdout=subprocess.PIPE,
    )
    try:
        assert result.returncode != 1
    except AssertionError as e:
        raise SecretNotFoundError(f"Error fetching `{str(secret)}`") from e

    return Secret.decode_raw_bytes_secret(input_bytes=result.stdout)


def edit_secret_file(file: pathlib.Path):
    editor = os.getenv("EDITOR", "vi")

    valid_json = False
    while True:
        subprocess.call(f"{editor} {file}", shell=True)
        # TODO: validate exit status?
        # TODO: add an option to skip validation
        try:
            with open(file) as f:
                json.load(f)
            valid_json = True
            break
        except json.decoder.JSONDecodeError as e:
            print(e)
            again = input("Try again [Y/n]: ")
            if again != "Y" and again != "":
                break

    if not valid_json:
        raise Exception("Unable to validate JSON")

