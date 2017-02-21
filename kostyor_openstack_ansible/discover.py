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

import collections

from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager

from kostyor.inventory.discover import ServiceDiscovery
from kostyor.rpc.app import app

# Ansible Inventory consists of groups each contains number of hosts.
# This is a map of Ansible groups to OpenStack services. In other words,
# all hosts of the following groups have the following services assigned
# to them.
_SERVICES_BY_INVENTORY_GROUPS = {
    'keystone': [
        'keystone-wsgi-admin',
        'keystone-wsgi-public',
    ],
    'glance_api': [
        'glance-api',
    ],
    'glance_registry': [
        'glance-registry',
    ],
    'nova_conductor': [
        'nova-conductor',
    ],
    'nova_scheduler': [
        'nova-scheduler',
    ],
    'nova_cert': [
        'nova-cert',
    ],
    'nova_console': [
        'nova-spicehtml5proxy',
        'nova-consoleauth',
    ],
    'nova_api_metadata': [
        'nova-api-metadata',
    ],
    'nova_api_os_compute': [
        'nova-api-os-compute',
    ],
    'nova_compute': [
        'nova-compute',
    ],
    'neutron_server': [
        'neutron-server',
    ],
    'neutron_openvswitch_agent': [
        'neutron-openvswitch-agent',
    ],
    'neutron_linuxbridge_agent': [
        'neutron-linuxbridge-agent',
    ],
    'neutron_l3_agent': [
        'neutron-l3-agent',
    ],
    'neutron_dhcp_agent': [
        'neutron-dhcp-agent',
    ],
    'neutron_metering_agent': [
        'neutron-metering-agent',
    ],
    'neutron_metadata_agent': [
        'neutron-metadata-agent',
    ],
    'cinder_api': [
        'cinder-api',
    ],
    'cinder_scheduler': [
        'cinder-scheduler',
    ],
    'cinder_volume': [
        'cinder-volume',
    ],
    'horizon': [
        'horizon-wsgi',
    ],
    'heat_api': [
        'heat-api',
    ],
    'heat_api_cfn': [
        'heat-api-cfn',
    ],
    'heat_api_cloudwatch': [
        'heat-api-cloudwatch',
    ],
    'heat_engine': [
        'heat-engine',
    ],
    'swift_proxy': [
        'swift-proxy-server',
    ],
    'swift_acc': [
        'swift-account-auditor',
        'swift-account-reaper',
        'swift-account-replicator',
        'swift-account-server',
    ],
    'swift_cont': [
        'swift-container-auditor',
        'swift-container-reconciler',
        'swift-container-replicator',
        'swift-container-server',
        'swift-container-sync',
        'swift-container-updater',
    ],
    'swift_obj': [
        'swift-object-auditor',
        'swift-object-expirer',
        'swift-object-reconstructor',
        'swift-object-replicator',
        'swift-object-server',
        'swift-object-updater',
    ],
}


@app.task
def _get_hosts():
    """Inspect OpenStack Ansible setup for hosts and services. Returned
    dictionary has a hostname as a key, and set of services as a value.
    Here's an example::

        {
            'host-1': [
                {'name': 'nova-conductor'},
                {'name': 'nova-api'},
            ],
            'host-2': [
                {'name': 'nova-compute'},
            ],
        }

    Please note, in some case we may return extra services due to bugs
    in OpenStack Ansible dynamic inventory which may produce extra items.
    Though they won't affect upgrade procedure, they might be a little
    misleading.
    """
    rv = collections.defaultdict(list)
    inventory = Inventory(DataLoader(), VariableManager())

    for group, services in _SERVICES_BY_INVENTORY_GROUPS.items():
        group = inventory.get_group(group)

        if group is None:
            continue

        for host in group.get_hosts():
            # TODO: Process services to be added as not of them may be
            #       applied to the current setup. E.g., Neutron may be
            #       configured to use openvswitch instead of linux bridges,
            #       while we always add both of them. It doesn't affect
            #       upgrade procedure, though, since services are used
            #       to build an upgrade order and no more.
            rv[host.get_vars()['physical_host']].extend((
                {'name': service} for service in services
            ))

    return rv


class Driver(ServiceDiscovery):

    def discover(self):
        return {
            'hosts': _get_hosts.delay().get(),
        }
