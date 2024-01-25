import difflib
import pathlib
import re
import subprocess
import tempfile

from gsm_editor import utils
from gsm_editor.exceptions import SecretNotFoundError
from gsm_editor.models import CommandConfig, Secret

# Create new secrets using this default string
DEFAULT_SECRET_STRING = "{\n}\n"


def edit_secret(config: CommandConfig):
    secret = Secret.from_command_config(config=config)
    with tempfile.NamedTemporaryFile() as temporary_file:
        file = pathlib.Path(temporary_file.name)
        try:
            decoded_secret = utils.get_secret_version(secret=secret)
            secret_exists = True
        except SecretNotFoundError:
            decoded_secret = DEFAULT_SECRET_STRING
            secret_exists = False

        # write decoded secret to temp file
        with open(file, 'r+') as f:
            f.write(decoded_secret)

        if secret_exists:
            original_shasum = utils.shasum(file)

            # Open temp_file in editor
            utils.edit_secret_file(file=file)

            new_shasum = utils.shasum(file)
            if new_shasum != original_shasum:
                utils.add_secret_version(secret=secret, file=file)
            else:
                print("No changes. Not pushing new version")

        else:
            utils.edit_secret_file(file=file)
            utils.create_secret(secret=secret, file=file)


def view_secret(config: CommandConfig):
    secret = Secret.from_command_config(config=config)
    decoded_secret = utils.get_secret_version(secret=secret)
    print(decoded_secret)


def list_secrets(config: CommandConfig):
    secret = Secret.from_command_config(config=config)
    subprocess.call(
        ["gcloud", "--project", secret.project_id, "secrets", "versions", "list",
         secret.secret_name]
    )


def name_secrets(config: CommandConfig):
    secret = Secret.from_command_config(config=config)
    full_names = subprocess.run(
        ["gcloud", "--project", secret.project_id, "secrets", "list",
         "--format=get(name)"],
        capture_output=True,
        text=True,
    )
    result = re.findall(rf"(?<={secret.env}-gke-)(.*)(?=-secrets)", full_names.stdout)
    print("\n".join(map(str, result)))


def diff_secrets(config: CommandConfig, version_a: str, version_b: str):
    secret_a = Secret(project_id=config.project_id, env=config.env, secret_id=config.secret_id, version=version_a)
    secret_b = Secret(project_id=config.project_id, env=config.env, secret_id=config.secret_id, version=version_b)

    decoded_secret_a = utils.get_secret_version(secret=secret_a).splitlines(keepends=True)
    decoded_secret_b = utils.get_secret_version(secret=secret_b).splitlines(keepends=True)

    diff = []
    for line in difflib.unified_diff(
            decoded_secret_a, decoded_secret_b,
            fromfile=str(secret_a),
            tofile=str(secret_b),
            lineterm=""):
        diff.append(line)
    if diff:
        print("\n".join(diff))
    else:
        print(f"No differences between `{str(secret_a)}` and `{str(secret_b)}`.")
