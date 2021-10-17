# coding: utf-8
from __future__ import unicode_literals

from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

import pytest
import os
import json

import testinfra.utils.ansible_runner

import pprint
pp = pprint.PrettyPrinter()

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def base_directory():
    """ ... """
    cwd = os.getcwd()

    if('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


@pytest.fixture()
def get_vars(host):
    """
        parse ansible variables
        - defaults/main.yml
        - vars/main.yml
        - molecule/${MOLECULE_SCENARIO_NAME}/group_vars/all/vars.yml
    """
    base_dir, molecule_dir = base_directory()

    file_defaults = "file={}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


@pytest.mark.parametrize("dirs", [
    "/etc/ansible/facts.d",
    "/opt/jolokia/",
    "/opt/jolokia/current/webapps/jolokia/WEB-INF/lib"
])
def test_directories(host, dirs):
    d = host.file(dirs)
    assert d.is_directory


def test_jolokia(host, get_vars):
    """
      test installed jolokia version
    """
    jolokia_version = get_vars.get("jolokia_version")

    jolokia_file = "/opt/jolokia/current/webapps/jolokia/WEB-INF/lib/jolokia-core-{version}.jar"
    jolokia_file = jolokia_file.format(version=jolokia_version)

    f = host.file(jolokia_file)
    assert f.is_file


@pytest.mark.parametrize("files", [
    "/opt/jolokia/current/webapps/jolokia/WEB-INF/web.xml",
    "/opt/jolokia/current/conf/server.xml",
    "/opt/jolokia/current/conf/tomcat-users.xml",
    "/opt/jolokia/current/bin/setenv.sh"
])
def test_files(host, files):
    f = host.file(files)
    assert f.is_file


def test_user(host):
    assert host.group("jolokia").exists
    assert host.user("jolokia").exists
    assert "jolokia" in host.user("jolokia").groups
    assert host.user("jolokia").shell == "/sbin/nologin"
    assert host.user("jolokia").home == "/opt/jolokia"


def test_service(host):
    service = host.service("jolokia")
    assert service.is_enabled
    assert service.is_running


@pytest.mark.parametrize("ports", [
    '127.0.0.1:8005',
    '0.0.0.0:8080',
    '0.0.0.0:22222',
])
def test_open_port(host, ports):

    for i in host.socket.get_listening_sockets():
        print(i)

    application = host.socket("tcp://%s" % (ports))
    assert application.is_listening


def test_request(host, get_vars):
    """
    """
    jolokia_version = get_vars.get('jolokia_version')
    cmd = host.run("curl http://localhost:8080/jolokia")

    if(cmd.succeeded):
        j = json.loads(cmd.stdout)

        version = j.get('value', {}).get('agent', '0')
        status = j.get('status')

        assert status == 200
        assert version == jolokia_version
    else:
        assert cmd.failed
