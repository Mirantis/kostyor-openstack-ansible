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

from kostyor_openstack_ansible.upgrades import base

from .common import get_fixture, get_inventory_instance


class TestGetServiceContainersForHost(object):

    _inventory = get_fixture('dynamic_inventory.json')

    def test_only_infra1_keystone_container(self):
        inventory = get_inventory_instance(self._inventory)

        component_hosts = base.get_component_hosts_on_node(
            inventory,
            {'name': 'keystone-wsgi-admin'},
            {'hostname': 'infra1'},
        )

        assert set([host.get_name() for host in component_hosts]) == set([
            'infra1_keystone_container-4d65b5ea',
        ])

    def test_only_infra2_nova_containers(self):
        inventory = get_inventory_instance(self._inventory)

        component_hosts = base.get_component_hosts_on_node(
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
        inventory = get_inventory_instance(self._inventory)

        component_hosts = base.get_component_hosts_on_node(
            inventory,
            {'name': 'nova-compute'},
            {'hostname': 'compute1'},
        )

        assert set([host.get_name() for host in component_hosts]) == set([
            'compute1',
        ])

    def test_no_keystone_on_compute(self):
        inventory = get_inventory_instance(self._inventory)

        component_hosts = base.get_component_hosts_on_node(
            inventory,
            {'name': 'keystone-wsgi-admin'},
            {'hostname': 'compute1'},
        )

        assert set([host.get_name() for host in component_hosts]) == set([])
