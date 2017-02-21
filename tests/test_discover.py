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

import mock
import pytest

from kostyor.rpc import app
from kostyor_openstack_ansible import discover

from .common import get_fixture, get_inventory_instance


class TestDriver(object):

    _inventory = get_fixture('dynamic_inventory.json')

    @pytest.fixture(autouse=True)
    def use_sync_tasks(self, monkeypatch):
        monkeypatch.setattr(app.app.conf, 'CELERY_ALWAYS_EAGER', True)

    @pytest.fixture(autouse=True)
    def use_fake_inventory(self, monkeypatch):
        monkeypatch.setattr(
            'kostyor_openstack_ansible.discover.Inventory',
            mock.Mock(
                return_value=get_inventory_instance(self._inventory)
            )
        )

    def test_discover(self):
        info = discover.Driver().discover()

        for hostname, services in info['hosts'].items():
            info['hosts'][hostname] = sorted(services, key=lambda v: v['name'])

        assert info == {
            'hosts': {
                'infra1': [
                    {'name': 'cinder-api'},
                    {'name': 'cinder-scheduler'},
                    {'name': 'glance-api'},
                    {'name': 'glance-registry'},
                    {'name': 'heat-api'},
                    {'name': 'heat-api-cfn'},
                    {'name': 'heat-api-cloudwatch'},
                    {'name': 'heat-engine'},
                    {'name': 'horizon-wsgi'},
                    {'name': 'keystone-wsgi-admin'},
                    {'name': 'keystone-wsgi-public'},
                    {'name': 'neutron-dhcp-agent'},
                    {'name': 'neutron-l3-agent'},
                    {'name': 'neutron-linuxbridge-agent'},
                    {'name': 'neutron-metadata-agent'},
                    {'name': 'neutron-metering-agent'},
                    {'name': 'neutron-openvswitch-agent'},
                    {'name': 'neutron-server'},
                    {'name': 'nova-api-metadata'},
                    {'name': 'nova-api-os-compute'},
                    {'name': 'nova-cert'},
                    {'name': 'nova-conductor'},
                    {'name': 'nova-consoleauth'},
                    {'name': 'nova-scheduler'},
                    {'name': 'nova-spicehtml5proxy'},
                ],
                'infra2': [
                    {'name': 'cinder-api'},
                    {'name': 'cinder-scheduler'},
                    {'name': 'glance-api'},
                    {'name': 'glance-registry'},
                    {'name': 'heat-api'},
                    {'name': 'heat-api-cfn'},
                    {'name': 'heat-api-cloudwatch'},
                    {'name': 'heat-engine'},
                    {'name': 'horizon-wsgi'},
                    {'name': 'keystone-wsgi-admin'},
                    {'name': 'keystone-wsgi-public'},
                    {'name': 'neutron-dhcp-agent'},
                    {'name': 'neutron-l3-agent'},
                    {'name': 'neutron-linuxbridge-agent'},
                    {'name': 'neutron-metadata-agent'},
                    {'name': 'neutron-metering-agent'},
                    {'name': 'neutron-openvswitch-agent'},
                    {'name': 'neutron-server'},
                    {'name': 'nova-api-metadata'},
                    {'name': 'nova-api-os-compute'},
                    {'name': 'nova-cert'},
                    {'name': 'nova-conductor'},
                    {'name': 'nova-consoleauth'},
                    {'name': 'nova-scheduler'},
                    {'name': 'nova-spicehtml5proxy'},
                ],
                'infra3': [
                    {'name': 'cinder-api'},
                    {'name': 'cinder-scheduler'},
                    {'name': 'glance-api'},
                    {'name': 'glance-registry'},
                    {'name': 'heat-api'},
                    {'name': 'heat-api-cfn'},
                    {'name': 'heat-api-cloudwatch'},
                    {'name': 'heat-engine'},
                    {'name': 'horizon-wsgi'},
                    {'name': 'keystone-wsgi-admin'},
                    {'name': 'keystone-wsgi-public'},
                    {'name': 'neutron-dhcp-agent'},
                    {'name': 'neutron-l3-agent'},
                    {'name': 'neutron-linuxbridge-agent'},
                    {'name': 'neutron-metadata-agent'},
                    {'name': 'neutron-metering-agent'},
                    {'name': 'neutron-openvswitch-agent'},
                    {'name': 'neutron-server'},
                    {'name': 'nova-api-metadata'},
                    {'name': 'nova-api-os-compute'},
                    {'name': 'nova-cert'},
                    {'name': 'nova-conductor'},
                    {'name': 'nova-consoleauth'},
                    {'name': 'nova-scheduler'},
                    {'name': 'nova-spicehtml5proxy'},
                ],
                'compute1': [
                    {'name': 'neutron-l3-agent'},
                    {'name': 'neutron-linuxbridge-agent'},
                    {'name': 'neutron-metadata-agent'},
                    {'name': 'neutron-openvswitch-agent'},
                    {'name': 'nova-compute'},
                ],
                'lvm-storage1': [
                    {'name': 'cinder-volume'},
                ],
            }
        }
