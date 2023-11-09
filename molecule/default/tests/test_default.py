# coding: utf-8
from __future__ import unicode_literals

from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

import json
import pytest
import os

import testinfra.utils.ansible_runner

HOST = 'instance'

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts(HOST)


def pp_json(json_thing, sort=True, indents=2):
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


def base_directory():
    """
    """
    cwd = os.getcwd()

    if 'group_vars' in os.listdir(cwd):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = f"molecule/{os.environ.get('MOLECULE_SCENARIO_NAME')}"

    return directory, molecule_directory


def read_ansible_yaml(file_name, role_name):
    """
    """
    read_file = None

    for e in ["yml", "yaml"]:
        test_file = "{}.{}".format(file_name, e)
        if os.path.isfile(test_file):
            read_file = test_file
            break

    return f"file={read_file} name={role_name}"


@pytest.fixture()
def get_vars(host):
    """
        parse ansible variables
        - defaults/main.yml
        - vars/main.yml
        - vars/${DISTRIBUTION}.yaml
        - molecule/${MOLECULE_SCENARIO_NAME}/group_vars/all/vars.yml
    """
    base_dir, molecule_dir = base_directory()
    distribution = host.system_info.distribution
    operation_system = None

    if distribution in ['debian', 'ubuntu']:
        operation_system = "debian"
    elif distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
        operation_system = "redhat"
    elif distribution in ['arch', 'artix']:
        operation_system = f"{distribution}linux"

    # print(" -> {} / {}".format(distribution, os))
    # print(" -> {}".format(base_dir))

    file_defaults      = read_ansible_yaml(f"{base_dir}/defaults/main", "role_defaults")
    file_vars          = read_ansible_yaml(f"{base_dir}/vars/main", "role_vars")
    file_distibution   = read_ansible_yaml(f"{base_dir}/vars/{operation_system}", "role_distibution")
    file_molecule      = read_ansible_yaml(f"{molecule_dir}/group_vars/all/vars", "test_vars")
    # file_host_molecule = read_ansible_yaml("{}/host_vars/{}/vars".format(base_dir, HOST), "host_vars")

    defaults_vars      = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars          = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    distibution_vars   = host.ansible("include_vars", file_distibution).get("ansible_facts").get("role_distibution")
    molecule_vars      = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")
    # host_vars          = host.ansible("include_vars", file_host_molecule).get("ansible_facts").get("host_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(distibution_vars)
    ansible_vars.update(molecule_vars)
    # ansible_vars.update(host_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def local_facts(host):
    """
      return local facts
    """
    return host.ansible("setup").get("ansible_facts").get("ansible_local").get("jolokia")


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
    # jolokia_version = get_vars.get("jolokia_version")

    jolokia_version = local_facts(host).get("version")

    jolokia_file = f"/opt/jolokia/current/webapps/jolokia/WEB-INF/lib/jolokia-core-{jolokia_version}.jar"

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
    assert host.user("jolokia").shell == "/usr/sbin/nologin"
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

    application = host.socket(f"tcp://{ports}")
    assert application.is_listening


def test_request(host, get_vars):
    """
    """
    jolokia_version = local_facts(host).get("version")
    # jolokia_version = get_vars.get('jolokia_version')
    cmd = host.run("curl http://localhost:8080/jolokia")

    if cmd.succeeded:
        j = json.loads(cmd.stdout)

        print(j)

        version = j.get('value', {}).get('agent', '0')
        status = j.get('status')

        assert status == 200
        assert version == jolokia_version
    else:
        assert cmd.failed
