# This file is part of OpenStack Ansible driver for Kostyor.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import os

import mock
import pytest

from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager

from kostyor.rpc import app, tasks

from kostyor_openstack_ansible import upgrade


def _get_inventory_fixture(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as fp:
        return json.load(fp)


@mock.patch('ansible.inventory.os.path.isfile', return_value=True)
@mock.patch('ansible.inventory.script.subprocess.Popen')
def _get_inventory_instance(inventory, popen, _):
    """Get an inventory instance based on input inventory dictionary.

    Due to poor Ansible design it's not easy to pass custom inventory
    programmatically. The thing is, we can a pass only a simple list
    of hosts programmatically without variables and so on. However,
    dynamic inventory provides much flexible functionality and allows
    to pass variables, subgroups and so on.

    In OpenStack Ansible we deal with dynamic inventory, so in order
    to simplify things and make tests much readable we need a way
    to retrieve an inventory instance based on produced JSON file
    by dynamic inventory.
    """
    stdout, stderr = json.dumps(inventory), ''

    popen().communicate = mock.Mock(return_value=(stdout, stderr))
    popen().returncode = 0

    loader = DataLoader()
    loader.path_exists = mock.Mock(return_value=True)
    loader.is_executable = mock.Mock(return_value=True)

    return Inventory(loader, VariableManager(), 'fake_dynamic_inventory.py')


class _host_ctx(object):
    """A simple context manager that mocks dbapi.get_host() to return a host
    with a specified hostname. It's important since this dbapi method is used
    internally to determine hostname of the node to be upgraded.

    :param hostname: a hostname of the host to be returned by dbapi.get_host()
    :type hostname: str
    """

    def __init__(self, hostname):
        self._patcher = mock.patch(
            'kostyor_openstack_ansible.upgrade.dbapi.get_host',
            return_value={
                'id': '1ecdf50f-16c2-4f7e-ba10-77bfeb2d2062',
                'cluster_id': '254dbd94-b426-484e-9155-4b60736cdef2',
                'hostname': hostname,
            })

    def __enter__(self):
        return self._patcher.start()

    def __exit__(self, type_, value, traceback):
        self._patcher.stop()


class TestGetServiceContainersForHost(object):

    _inventory = _get_inventory_fixture('dynamic_inventory.json')

    def test_only_infra1_keystone_container(self):
        inventory = _get_inventory_instance(self._inventory)

        component_hosts = upgrade._get_component_hosts_on_node(
            inventory,
            {'name': 'keystone-wsgi-admin'},
            {'hostname': 'infra1'},
        )

        assert set([host.get_name() for host in component_hosts]) == set([
            'infra1_keystone_container-4d65b5ea',
        ])

    def test_only_infra2_nova_containers(self):
        inventory = _get_inventory_instance(self._inventory)

        component_hosts = upgrade._get_component_hosts_on_node(
            inventory,
            {'name': 'nova-conductor'},
            {'hostname': 'infra2'},
        )

        hosts = set([host.get_name() for host in component_hosts])
        assert hosts == set([
            'infra2_nova_api_metadata_container-a542f3a5',
            'infra2_nova_api_os_compute_container-d088a5c5',
            'infra2_nova_cert_container-f4bebee6',
            'infra2_nova_conductor_container-c9d5c8ec',
            'infra2_nova_console_container-14f4435d',
            'infra2_nova_scheduler_container-ea104a41',
        ])

    def test_only_compute1_nova_on_host(self):
        inventory = _get_inventory_instance(self._inventory)

        component_hosts = upgrade._get_component_hosts_on_node(
            inventory,
            {'name': 'nova-compute'},
            {'hostname': 'compute1'},
        )

        assert set([host.get_name() for host in component_hosts]) == set([
            'compute1',
        ])

    def test_no_keystone_on_compute(self):
        inventory = _get_inventory_instance(self._inventory)

        component_hosts = upgrade._get_component_hosts_on_node(
            inventory,
            {'name': 'keystone-wsgi-admin'},
            {'hostname': 'compute1'},
        )

        assert set([host.get_name() for host in component_hosts]) == set([])


class TestDriver(object):

    _inventory = _get_inventory_fixture('dynamic_inventory.json')

    def setup(self):
        self._celery_eager = app.app.conf['CELERY_ALWAYS_EAGER']
        app.app.conf['CELERY_ALWAYS_EAGER'] = True

        self._patchers = []
        self.driver = upgrade.Driver()

        patcher = mock.patch(
            'kostyor_openstack_ansible.upgrade.Inventory',
            return_value=_get_inventory_instance(self._inventory)
        )
        self.inventory = patcher.start()()
        self._patchers.append(patcher)

        patcher = mock.patch(
            'kostyor_openstack_ansible.upgrade.PlaybookExecutor')
        self.executor = patcher.start()
        self._patchers.append(patcher)

        self.executor.return_value.run.return_value = 0

    def teardown(self):
        for patcher in self._patchers:
            patcher.stop()
        app.app.conf['CELERY_ALWAYS_EAGER'] = self._celery_eager

    @mock.patch('kostyor.rpc.tasks.execute.si', return_value=tasks.noop.si())
    def test_pre_upgrade_hook(self, execute):
        self.driver.pre_upgrade_hook(mock.Mock())()

        execute.assert_called_once_with(
            '/opt/openstack-ansible/scripts/bootstrap-ansible.sh',
            cwd='/opt/openstack-ansible')

        assert self.executor.call_args_list == [
            mock.call(
                playbooks=['/opt/openstack-ansible/scripts/upgrade-utilities'
                           '/playbooks/ansible_fact_cleanup.yml'],
                inventory=self.inventory,
                variable_manager=mock.ANY,
                loader=mock.ANY,
                options=mock.ANY,
                passwords={}),
            mock.call(
                playbooks=['/opt/openstack-ansible/scripts/upgrade-utilities'
                           '/playbooks/deploy-config-changes.yml'],
                inventory=self.inventory,
                variable_manager=mock.ANY,
                loader=mock.ANY,
                options=mock.ANY,
                passwords={}),
            mock.call(
                playbooks=['/opt/openstack-ansible/scripts/upgrade-utilities'
                           '/playbooks/user-secrets-adjustment.yml'],
                inventory=self.inventory,
                variable_manager=mock.ANY,
                loader=mock.ANY,
                options=mock.ANY,
                passwords={}),
            mock.call(
                playbooks=['/opt/openstack-ansible/scripts/upgrade-utilities'
                           '/playbooks/pip-conf-removal.yml'],
                inventory=self.inventory,
                variable_manager=mock.ANY,
                loader=mock.ANY,
                options=mock.ANY,
                passwords={}),
            mock.call(
                playbooks=['/opt/openstack-ansible/playbooks'
                           '/repo-install.yml'],
                inventory=self.inventory,
                variable_manager=mock.ANY,
                loader=mock.ANY,
                options=mock.ANY,
                passwords={}),
        ]

    def test_start_upgrade_runs_playbook(self):
        with _host_ctx('compute1') as host:
            self.driver.start_upgrade(
                mock.Mock(),
                {
                    'name': 'nova-compute',
                    'host_id': host['id'],
                })()

        self.executor.assert_called_once_with(
            playbooks=['/opt/openstack-ansible/playbooks/os-nova-install.yml'],
            inventory=self.inventory,
            variable_manager=mock.ANY,
            loader=mock.ANY,
            options=mock.ANY,
            passwords={},
        )

        assert set([h.get_name() for h in self.inventory.get_hosts()]) == set([
            'compute1',
        ])

    def test_start_upgrade_runs_playbook_once_on_one_host(self):
        with _host_ctx('infra2') as host:
            self.driver.start_upgrade(
                mock.Mock(),
                {
                    'name': 'nova-api',
                    'host_id': host['id'],
                })()
            self.driver.start_upgrade(
                mock.Mock(),
                {
                    'name': 'nova-conductor',
                    'host_id': host['id'],
                })()

        self.executor.assert_called_once_with(
            playbooks=['/opt/openstack-ansible/playbooks/os-nova-install.yml'],
            inventory=self.inventory,
            variable_manager=mock.ANY,
            loader=mock.ANY,
            options=mock.ANY,
            passwords={},
        )

        assert set([h.get_name() for h in self.inventory.get_hosts()]) == set([
            'infra2_nova_api_metadata_container-a542f3a5',
            'infra2_nova_api_os_compute_container-d088a5c5',
            'infra2_nova_cert_container-f4bebee6',
            'infra2_nova_conductor_container-c9d5c8ec',
            'infra2_nova_console_container-14f4435d',
            'infra2_nova_scheduler_container-ea104a41',
        ])

    def test_start_upgrade_skip_not_supported_service(self):
        with _host_ctx('infra1') as host:
            self.driver.start_upgrade(
                mock.Mock(),
                {
                    'name': 'not-supported-service',
                    'host_id': host['id'],
                })()

        self.executor.assert_not_called()

    def test_raise_exception_on_error(self):
        self.executor.return_value.run.return_value = 42

        with pytest.raises(Exception) as excinfo:
            self.test_start_upgrade_runs_playbook()

        assert str(excinfo.value) == (
            'Playbook "/opt/openstack-ansible/playbooks/os-nova-install.yml" '
            'has been finished with errors. Exit code is "42".'
        )
