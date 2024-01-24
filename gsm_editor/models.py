import base64
from argparse import Namespace
from dataclasses import dataclass


@dataclass
class CommandConfig:
    action: str
    project_id: str
    env: str
    secret_id: str | None
    version: str | None

    @classmethod
    def from_parser_args(cls, parser_args: Namespace) -> 'CommandConfig':
        # Deal with optional arguments
        secret_id = parser_args.secret if "secret" in parser_args else None
        version = parser_args.version if "version" in parser_args else None
        return CommandConfig(action=parser_args.action,
                             project_id=parser_args.project,
                             env=parser_args.env,
                             secret_id=secret_id,
                             version=version,
                             )


@dataclass
class Secret:
    project_id: str
    env: str
    secret_id: str | None
    version: str | None

    @classmethod
    def decode_raw_bytes_secret(cls, input_bytes: bytes) -> str:
        # to deal with possible binary data, google suggests the following transforms:
        # (see: https://cloud.google.com/sdk/gcloud/reference/secrets/versions/access)
        # Replaces ('_') with ('/') and ('-') with ('+')
        translation_table = bytes.maketrans(b'_-', b'/+')
        translated_result = input_bytes.translate(translation_table)
        return base64.b64decode(translated_result).decode("utf8")

    @property
    def secret_name(self) -> str:
        return f"{self.env}-gke-{self.secret_id}-secrets"

    def __str__(self) -> str:
        return f"{self.project_id}/{self.secret_name}:{self.version}"

    @classmethod
    def from_command_config(cls, config: CommandConfig) -> 'Secret':
        return Secret(project_id=config.project_id,
                      env=config.env,
                      secret_id=config.secret_id,
                      version=config.version,
                      )
