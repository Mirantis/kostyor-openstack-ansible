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

from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager


def get_fixture(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as fp:
        return json.load(fp)


@mock.patch('ansible.inventory.os.path.isfile', return_value=True)
@mock.patch('ansible.inventory.script.subprocess.Popen')
def get_inventory_instance(inventory, popen, _):
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


class host_ctx(object):
    """A simple context manager that mocks dbapi.get_host() to return a host
    with a specified hostname. It's important since this dbapi method is used
    internally to determine hostname of the node to be upgraded.

    :param hostname: a hostname of the host to be returned by dbapi.get_host()
    :type hostname: str
    """

    def __init__(self, hostname):
        self._patcher = mock.patch(
            'kostyor_openstack_ansible.upgrades.base.dbapi.get_host',
            return_value={
                'id': '1ecdf50f-16c2-4f7e-ba10-77bfeb2d2062',
                'cluster_id': '254dbd94-b426-484e-9155-4b60736cdef2',
                'hostname': hostname,
            })

    def __enter__(self):
        return self._patcher.start()

    def __exit__(self, type_, value, traceback):
        self._patcher.stop()
