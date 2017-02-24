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

from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager

from kostyor.rpc import tasks
from kostyor.rpc.app import app

from . import base


@app.task(bind=True, base=tasks.execute.__class__)
def _run_playbook(self, playbook, cwd=None, ignore_errors=False):
    return super(_run_playbook.__class__, self).run(
        [
            '/usr/local/bin/openstack-ansible', playbook,
        ],
        cwd=cwd,
        ignore_errors=ignore_errors,
    )


@app.task(bind=True, base=tasks.execute.__class__)
def _run_playbook_for(self, playbook, nodes, service, cwd=None,
                      ignore_errors=False):
    inventory = Inventory(DataLoader(), VariableManager())
    hosts = [
        host.get_vars()['inventory_hostname']
        for host in base.get_component_hosts_on_nodes(
            inventory, service, nodes
        )
    ]

    return super(_run_playbook_for.__class__, self).run(
        [
            '/usr/local/bin/openstack-ansible', playbook,
            '-l', ','.join(hosts)
        ],
        cwd=cwd,
        ignore_errors=ignore_errors,
    )


class Driver(base.Driver):

    _run_playbook = _run_playbook
    _run_playbook_for = _run_playbook_for
