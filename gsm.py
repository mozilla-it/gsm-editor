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

    Tips:

    - Use your preferred code editor:
      Define an `EDITOR` environment variable in your local environment to override the
      default `vi` value.
      Examples: `nano`, `vim`, `code`.
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
import sys
from argparse import ArgumentParser

from gsm_editor import commands
from gsm_editor.models import CommandConfig


def add_default_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "-p", "--project", type=str, required=True, help="GCP project id"
    )

    parser.add_argument(
        "-e",
        "--env",
        type=str,
        choices=["qa", "dev", "stage", "prod", "test", "preview"],
        required=True,
        help="secret env",
    )


def add_select_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "-s",
        "--secret",
        type=str,
        default="app",
        required=False,
        help='Custom secret identifier (default is "app")',
    )

    parser.add_argument(
        "-v",
        "--version",
        type=str,
        default="latest",
        required=False,
        help="Version of the secret to select",
    )


def add_parser_args(parser: ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="action", help="Secret action:")
    edit = subparsers.add_parser("edit", help="Edit a secret")
    add_default_arguments(parser=edit)
    add_select_arguments(parser=edit)

    view = subparsers.add_parser("view", help="Display secret content in the terminal")
    add_default_arguments(parser=view)
    add_select_arguments(parser=view)

    list_secrets = subparsers.add_parser("list", help="List all managed secrets in a project")
    add_default_arguments(parser=list_secrets)
    add_select_arguments(parser=list_secrets)

    diff = subparsers.add_parser("diff",
                                 help="Display differences between secret versions")
    add_default_arguments(parser=diff)
    diff.add_argument(
        "-s",
        "--secret",
        type=str,
        default="app",
        required=False,
        help='custom secret identifier (default is "app")',
    )
    diff.add_argument(
        "version_a",
        type=str,
        help="Version to compare",
    )
    diff.add_argument(
        "version_b",
        type=str,
        help="Other version to compare",
    )

    names = subparsers.add_parser("names", help="Display managed secret names")
    add_default_arguments(parser=names)


def get_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    add_parser_args(parser=parser)

    return parser


if __name__ == "__main__":
    parser = get_parser()

    # Print help if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()
        config = CommandConfig.from_parser_args(args)

        match config.action:
            case "edit":
                commands.edit_secret(config=config)
            case "view":
                commands.view_secret(config=config)
            case "list":
                commands.list_secrets(config=config)
            case "names":
                commands.name_secrets(config=config)
            case "diff":
                commands.diff_secrets(config=config, version_a=args.version_a, version_b=args.version_b)
