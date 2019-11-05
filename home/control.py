#!/usr/bin/env python3

"""
Dhall Code Generator
"""

import os
import git # type:ignore
import click
from home.service import Service

DEPENDENCIES = {
    'dhall-kubernetes': 'https://github.com/dhall-lang/dhall-kubernetes.git',
    'prelude': 'https://github.com/dhall-lang/dhall-lang.git'
}

SERVICE_ARGUMENT = click.argument('services', nargs=-1, type=click.Path(exists=True, file_okay=False))

@click.group()
def cli():
  '''entrypoint for homectl'''

@cli.command()
def init():
  '''Initializes the homectl, by pulling all needed dependencies'''

  for key, value in DEPENDENCIES.items():
    path = "dhall/dependencies"
    if not os.path.exists(path):
      os.makedirs((path))
    repository = git.cmd.Git(path)
    try:
      print("Checking {}".format(key))
      repository.clone(value)
      print("Cloned {}".format(key))
    except git.GitCommandError:
      repository.pull()
      print("Pulled {}".format(key))
  print("Dependencies pulled...")

@cli.command()
@SERVICE_ARGUMENT
@click.option('--secrets', is_flag=True, help='generates secrets')
def generate(services, generate_secrets):
  '''generates code needed for deploying a service'''
  for service_name in services:
    Service(service_name).generate(generate_secrets=generate_secrets)

@cli.command()
@SERVICE_ARGUMENT
def apply(services):
  '''deploys the service'''
  for service_name in services:
    Service(service_name).apply()

@cli.command()
@SERVICE_ARGUMENT
def delete(services):
  '''deletes the deployed service'''
  for service_name in services:
    Service(service_name).delete()
