"""Command to help users assume roles in different accounts."""

import os
import re
from getpass import getuser
from uuid import uuid1

import boto3
from botocore.exceptions import ClientError
import click


ROLE_FORMAT = "arn:aws:iam::{account_id}:role/{role}"
URL_FORMAT = "https://signin.aws.amazon.com/switchrole?account={account_id}&roleName={role_name}&displayName={account}%20-%20{role}"  # pylint: disable=line-too-long
OVERWRITE_ENVS = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]


@click.command()
@click.argument("account", envvar="BYHT_ASSUME_ACCOUNT", required=False)
@click.argument("role", envvar="BYHT_ASSUME_ROLE", required=False)
@click.option("--duration", "-d", envvar="BYHT_ASSUME_DURATION", default='1h',
              help="Duration in seconds or with units (h, m, s)")
@click.option("--token", "-t", help="MFA token")
@click.option("--url", default=False, is_flag=True,
              help="Provide URL instead of environment variables")
def handle(account, role, duration, token, url):  # pylint: disable=too-many-arguments,too-many-locals,line-too-long
    """Switch between roles in Neo accounts with MFA.

    Environment variables BYHT_ASSUME_ACCOUNT, BYHT_ASSUME_ROLE, and BYHT_ASSUME_DURATION
    can be used to specify default values for assume.
    """

    if not account:
        account = click.prompt("Account", err=True)

    if not role:
        role = click.prompt("Role", err=True)

    if not all([account, role]):
        click.echo("You must provide ACCOUNT, and ROLE to continue", err=True)
        exit(1)

    #os.environ = {k: v
    #              for k, v in os.environ.items()
    #              if os.environ[k] in OVERWRITE_ENVS}

    account_id = account
    role_name = role
    duration = str_to_seconds(duration)

    if url:
        click.echo(URL_FORMAT.format(account_id=account_id,
                                     account=account,
                                     role_name=role_name,
                                     role=role), err=True)
        exit(0)

    role_arn = ROLE_FORMAT.format(account_id=account_id, role=role_name)

    click.echo(f"# Assuming {role_arn}", err=True)

    assume_args = {
        "RoleArn": role_arn,
        "RoleSessionName": ("%s_BYHT_assume_%s" % (getuser(), str(uuid1())))[:64],
        "DurationSeconds": duration,
    }

    sts = boto3.client("sts")

    try:
        caller = boto3.client("sts").get_caller_identity()
        username = caller.get("Arn", "").split("/")[-1]

        if not username:
            click.echo("# Error getting identity", err=True)
            exit(1)

        if token:
            iam = boto3.client("iam")
            devices = iam.list_mfa_devices(UserName=username)

            assume_args["SerialNumber"] = devices["MFADevices"][0]["SerialNumber"]
            assume_args["TokenCode"] = token

        tokens = sts.assume_role(**assume_args)
    except ClientError as exc:
        click.echo(f"Error: {exc}", err=True)
        exit(1)
    except KeyError:
        click.echo("# Check that MFA is enabled.")
        exit(1)

    click.echo(f"export AWS_ACCESS_KEY_ID={tokens['Credentials']['AccessKeyId']}")
    click.echo(f"export AWS_SECRET_ACCESS_KEY={tokens['Credentials']['SecretAccessKey']}")
    click.echo(f"export AWS_SESSION_TOKEN={tokens['Credentials']['SessionToken']}")
    click.echo("# Session expires: %s (%d seconds)" % (
        tokens["Credentials"]["Expiration"].isoformat(),
        duration), err=True)


def str_to_seconds(duration):
    """Convert a string of format "XdXhXmXs" to seconds or return the integer value"""
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}

    matches = re.findall("^([0-9-]+[%s])+$" % "".join(units.keys()), duration.lower())

    if not matches:
        return int(duration)

    return sum([int(match.strip()[:-1]) * units.get(match.strip()[-1], 0)
                for match in matches
                if match.strip()[-1] in units.keys()])


if __name__ == "__main__":
    handle()
