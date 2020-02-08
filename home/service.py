'''
Representation of a service. Contains methods for generating, applying, and deleting services
'''

import sys
import os
import subprocess
import json
import re
from typing import List, Tuple

OUTPUT_FILE_TYPE = "yaml"
PACKAGE_FILE_NAME = "homectl.json"

class Service:
  '''Representation of generatable resources'''

  path: str

  def __init__(self, path):
    self.path = path
    self.dhall = os.path.isfile(f"{self.path}/values.dhall")
    self.helm = os.path.isfile(f"{self.path}/helm.yaml")

  def _generate_dhall(self) -> bool:
    print("Dhall Resources:")

    result = subprocess.run(
      ["dhall-to-yaml", "--omitEmpty", "--documents"],
      capture_output=True,
      text=True,
      input=f"./{self.path}/values.dhall"
    )

    if result.returncode != 0:
      print(f"{self.path} ✗")
      print(result.stderr, file=sys.stderr)
      return False

    output_file_name = f"output.{OUTPUT_FILE_TYPE}"

    with open(f"{self.path}/{output_file_name}", 'w') as output_file:
      output_file.write(result.stdout)

    print(f"{self.path} ✓")

    return True

  def _apply_dhall(self) -> bool:
    status = True

    result = subprocess.run(
      ["kubectl", "apply", "-f", f"{self.path}/output.yaml"],
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
      ["kubectl", "delete", "-f", f"{self.path}/output.yaml"],
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

  def generate(self) -> bool:
    '''Generates all resources defined in the service'''
    status = True

    print(f"Creating Resources for {self.path}:")

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
