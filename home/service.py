'''
Representation of a service. Contains methods for generating, applying, and deleting services
'''

import sys
import os
import subprocess
import json
import re
from typing import List, Tuple
from jinja2 import PackageLoader, Environment
from pkg_resources import resource_filename

OUTPUT_FILE_TYPE = "yaml"
PACKAGE_FILE_NAME = "homectl.json"

class Service:
  '''Representation of generatable resources'''

  path: str

  def __init__(self, path):
    try:
      with open(f"{path}/{PACKAGE_FILE_NAME}") as json_data:
        package = json.load(json_data)
    except FileNotFoundError:
      print(f"Could not find {PACKAGE_FILE_NAME} in {path}")
      return

    self.path = path

    self.dhall = package['dhall'] if 'dhall' in package else None
    self.helm = package['helm'] if 'helm' in package else None

  def _check_dhall_validity(self, key) -> bool:
    if key not in self.dhall:
      return False

    return bool(self.dhall[key])

  def _run_dhall(self, resource: str, secrets: List[Tuple[str, str]] = None) -> bool:
    resource_type = self._get_resource_type(resource)

    if not resource_type:
      return False

    package_loader = PackageLoader('home', '')
    template_env = Environment(loader=package_loader)
    dhall_input = template_env.get_template('resource_creation.jinja')
    rendered_dhall_input = dhall_input.render(
      values=f"./{self.path}/{self.dhall['source']}",
      resource_type=resource_type,
      resource=resource,
      secrets=secrets
    )

    result = subprocess.run(
      ["dhall-to-yaml", "--omitNull", "--documents"],
      capture_output=True,
      text=True,
      input=rendered_dhall_input
    )

    if result.returncode != 0:
      print(f"{resource} ✗")
      print(result.stderr, file=sys.stderr)
      return False

    output_file_name = f"{resource}.{OUTPUT_FILE_TYPE}"

    if not os.path.exists(f"{self.path}/output"):
      os.makedirs(f"{self.path}/output")

    with open(f"{self.path}/output/{output_file_name}", 'w') as output_file:
      output_file.write(result.stdout)

    print(f"{resource} ✓")

    return True

  @staticmethod
  def _get_resource_type(resource) -> str:
    # for strings that look like "resource_type-03", extract "resource_type"
    matches = re.search(r'([^-\s]+)(-\d+)?', resource)

    if not matches:
      print(f"Could not determine resource type for {resource}")
      print(f"{resource} ✗")
      return ""

    return matches.group(1)

  def _generate_dhall(self) -> bool:
    print("Dhall Resources:")

    status = True

    if not self._check_dhall_validity('resources'):
      print(f"WARNING: no resources specified for {self.path}")
      return True

    for resource in self.dhall['resources']:
      status = self._run_dhall(resource) and status

    return status

  def _generate_secret(self) -> bool:
    print("Dhall Secrets:")

    status = True

    if not self._check_dhall_validity('secrets'):
      print(f"WARNING: no secrets specified for {self.path}")
      return True

    for resource in self.dhall['secrets']:
      secret_keys = self.dhall['secrets'][resource]


      secrets = []
      for secret_key in secret_keys:
        secret_value = input(f"Enter value for {secret_key}:\n")
        secrets.append((secret_key, secret_value))
      status = self._run_dhall(resource, secrets)

    return status

  def _apply_dhall(self) -> bool:
    status = True

    result = subprocess.run(
      ["kubectl", "apply", "-f", f"{self.path}/output"],
      capture_output=True,
      text=True
    )

    if result.returncode != 0:
      print(f"{self.path} ✗")
      print(result.stderr, file=sys.stderr)
      status = False
    else:
      print(f"{self.path} ✓")
      print(result.stdout)

    return status

  def _delete_dhall(self) -> bool:
    status = True

    result = subprocess.run(
      ["kubectl", "delete", "-f", f"{self.path}/output"],
      capture_output=True,
      text=True
    )

    if result.returncode != 0:
      print(f"{self.path} ✗")
      print(result.stderr, file=sys.stderr)
      status = False
    else:
      print(f"{self.path} ✓")
      print(result.stdout)

    return status

  def _apply_helm(self) -> bool:
    print("Helm Resources:")

    status = True

    namespace = self.helm['namespace'] if 'namespace' in self.helm and self.helm['namespace'] else 'default'

    result = subprocess.run(
      ["helm", "install", self.helm['source'], '-n', self.helm['name'], '--namespace', namespace, '-f', f"./{self.path}/{self.helm['values']}"],
      capture_output=True,
      text=True
    )

    if result.returncode != 0:
      print(f"{self.helm['name']} ✗")
      print(result.stderr, file=sys.stderr)
      status = False
    else:
      print(f"{self.helm['name']} ✓")
      print(result.stdout)

    return status

  def _delete_helm(self) -> bool:
    print("Helm Resources:")

    status = True

    result = subprocess.run(
      ["helm", "delete", self.helm['name'], '--purge'],
      capture_output=True,
      text=True
    )

    if result.returncode != 0:
      print(f"{self.helm['name']} ✗")
      print(result.stderr, file=sys.stderr)
      status = False
    else:
      print(f"{self.helm['name']} ✓")
      print(result.stdout)

    return status

  def generate(self, generate_secrets=False) -> bool:
    '''Generates all resources defined in the service'''
    status = True

    print(f"Creating Resources for {self.path}:")

    if generate_secrets:
      status = self._generate_secret() and status

    if self.dhall:
      status = self._generate_dhall() and status

    return status

  def apply(self) -> bool:
    '''Applies all resources defined in the service'''
    status = True
    if self.dhall:
      status = self._apply_dhall() and status

    if self.helm:
      status = self._apply_helm() and status

    return status

  def delete(self) -> bool:
    '''Deletes resources defined in the service'''
    status = True
    if self.helm:
      status = self._delete_helm() and status

    if self.dhall:
      status = self._delete_dhall() and status

    return status
