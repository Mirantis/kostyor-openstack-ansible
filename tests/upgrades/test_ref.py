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

import os

import mock
import pytest

from kostyor.rpc import app, tasks
from kostyor_openstack_ansible.upgrades import ref

from ..common import get_fixture, get_inventory_instance, get_hosts


class TestDriver(object):

    _inventory = get_fixture('dynamic_inventory.json')

    @pytest.fixture(autouse=True)
    def use_sync_tasks(self, monkeypatch):
        monkeypatch.setattr(app.app.conf, 'CELERY_ALWAYS_EAGER', True)

    @pytest.fixture(autouse=True)
    def use_fake_inventory(self, monkeypatch):
        self.inventory = get_inventory_instance(self._inventory)

        monkeypatch.setattr(
            'kostyor_openstack_ansible.upgrades.ref.Inventory',
            mock.Mock(
                return_value=self.inventory
            )
        )

    @pytest.fixture(autouse=True)
    def use_fake_executor(self, monkeypatch):
        self.executor = mock.Mock()
        self.executor.return_value.run.return_value = 0

        monkeypatch.setattr(
            'kostyor_openstack_ansible.upgrades.ref.PlaybookExecutor',
            self.executor
        )

    def setup(self):
        self.driver = ref.Driver()

    @mock.patch('kostyor_openstack_ansible.upgrades.ref.os.chdir')
    @mock.patch('kostyor.rpc.tasks.execute.si', return_value=tasks.noop.si())
    def test_pre_upgrade(self, execute, chdir):
        self.driver.pre_upgrade()()

        execute.assert_called_once_with(
            '/opt/openstack-ansible/scripts/bootstrap-ansible.sh',
            cwd='/opt/openstack-ansible')

        assert chdir.call_args_list == [
            mock.call('/opt/openstack-ansible/playbooks'),
            mock.call(os.getcwd()),
        ]

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

    def test_start_runs_playbook(self):
        self.driver.start({'name': 'nova-compute'}, get_hosts('compute1'))()

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

    def test_start_runs_playbook_on_few_hosts(self):
        self.driver.start(
            {'name': 'horizon-wsgi'}, get_hosts('infra1', 'infra2'))()

        self.executor.assert_called_once_with(
            playbooks=[
                '/opt/openstack-ansible/playbooks/os-horizon-install.yml'],
            inventory=self.inventory,
            variable_manager=mock.ANY,
            loader=mock.ANY,
            options=mock.ANY,
            passwords={},
        )

        assert set([h.get_name() for h in self.inventory.get_hosts()]) == set([
            'infra1_horizon_container-afb604da',
            'infra2_horizon_container-b7a45742',
        ])

    def test_start_runs_playbook_once_on_one_host(self):
        hosts = get_hosts('infra2')

        self.driver.start({'name': 'nova-api'}, hosts)()
        self.driver.start({'name': 'nova-conductor'}, hosts)()

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

    def test_start_runs_playbook_once_on_few_hosts(self):
        host1, host2 = get_hosts('infra1', 'infra2')

        # The second .start(...) must trigger playbook only for host2 as
        # host1 was upgrades by first call.
        self.driver.start({'name': 'nova-api'}, [host1])()
        self.driver.start({'name': 'nova-conductor'}, [host1, host2])()

        self.executor.assert_called_with(
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

    def test_start_skip_not_supported_service(self):
        self.driver.start({'name': 'unknown-service'}, get_hosts('infra1'))()

        self.executor.assert_not_called()

    def test_raise_exception_on_error(self):
        self.executor.return_value.run.return_value = 42

        with pytest.raises(Exception) as excinfo:
            self.test_start_runs_playbook()

        assert str(excinfo.value) == (
            'Playbook "/opt/openstack-ansible/playbooks/os-nova-install.yml" '
            'has been finished with errors. Exit code is "42".'
        )
