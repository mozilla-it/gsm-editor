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

import os, subprocess, argparse, tempfile, atexit, json

def create_secret(project_id, secret_id, filename):
    """
    Create a new secret with the given name. A secret is a logical wrapper
    around a collection of secret versions. Secret versions hold the actual
    secret material.
    """

    # FIXME: is an exception raised if this fails? if not, then look at return code
    result = subprocess.run(["gcloud", "--project", project_id, "secrets", "create", secret_id, "--data-file", filename])


def add_secret_version(project_id, secret_id, filename):
    """
    Add a new secret version to the given secret with the provided payload.
    """

    # FIXME: is an exception raised if this fails? if not, then look at return code
    result = subprocess.run(["gcloud", "--project", project_id, "secrets", "versions", "add", secret_id, "--data-file", filename])

def list_secret_versions(project_id, secret_id):
    result = subprocess.call(["gcloud", "--project", project_id, "secrets", "versions", "list", secret_id])

def access_secret_version(project_id, secret_id, filename, version):
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """

    result = subprocess.run(["gcloud",
                             "--project", project_id,
                             "secrets",
                             "versions",
                             "access",
                             version,
                             "--secret", secret_id,
                             "--format=get(payload.data)"], stdout=subprocess.PIPE)
    if result.returncode == 1:
        #print(f"No such secret {project_id} {secret_id} {version}")
        return 0

    # to deal with possible binary data, google suggests the following transforms:
    # (see: https://cloud.google.com/sdk/gcloud/reference/secrets/versions/access)
    result_tr  = subprocess.run(["tr", "_-", "/+"], input=result.stdout, stdout=subprocess.PIPE)
    result_b64 = subprocess.run(["base64", "-d"], input=result_tr.stdout, stdout=open(filename, 'w', 1))
    return 1

def cat_secret(project_id, secret_id, filename, version):
    with open(filename, 'r') as f:
        print(f.read())

def edit_secret(filename):
    editor = os.getenv('EDITOR', 'vi')

    valid_json = False

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("action", help="action: edit|view|list|diff")
    parser.add_argument("-p", "--project", type=str, required=True, help="id of the GCP project")
    parser.add_argument("-e", "--env", type=str, required=True, help="env of the secret (typically 'dev', 'stage', or 'prod')")
    parser.add_argument("-s", "--secret", type=str, required=False, help="id of the secret to create/change, don't use this")
    parser.add_argument("-v", "--version", type=str, required=False, help="version of the secret to create/change")
    args = parser.parse_args()

    if not args.secret:
        secret_name = f"{args.env}-gke-app-secrets"
    else:
        secret_name = f"{args.env}-{args.secret}"

    version = args.version
    if not version:
        version = "latest"

    (tempfile_fd, tempfile_path) = tempfile.mkstemp()

    # remove the tempfile on expected or unexpected program exit
    def exit_handler():
        os.unlink(tempfile_path)
    atexit.register(exit_handler)

    if args.action == "edit":
        is_existing_secret = access_secret_version(args.project, secret_name, tempfile_path, version)
        edit_secret(tempfile_path)
        if is_existing_secret:
            add_secret_version(args.project, secret_name, tempfile_path)
        else:
            create_secret(args.project, secret_name, tempfile_path)
    elif args.action == "view":
        access_secret_version(args.project, secret_name, tempfile_path, version)
        cat_secret(args.project, secret_name, tempfile_path, version)
    elif args.action == "list":
        list_secret_versions(args.project, secret_name)
    elif args.action == "diff":
        print("UNIMPLEMENTED. sorry.")
