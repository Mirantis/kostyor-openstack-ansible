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

import celery

from kostyor.db import api as dbapi
from kostyor.rpc import tasks
from kostyor.upgrades.drivers import base


def _get_component_from_service(service):
    # OpenStack services has the following naming format: '{component}-*',
    # so we can use first part before dash as a component name.
    return service['name'].split('-')[0]


def get_component_hosts_on_node(inventory, service, host):
    component = _get_component_from_service(service)
    variables = inventory.get_vars(host['hostname'])
    hostgroup = inventory.get_group(variables['container_types'])

    # Despite the fact that 'container_types' host variable always exists,
    # it may points to non-existing group. For instance, compute hosts
    # have 'container_types=computeX-host_containers' but the group
    # doesn't exist within inventory.
    if hostgroup is not None:
        containers = hostgroup.get_hosts()
    else:
        containers = []

    # Not all services are running in containers, so we want to add the
    # host itself into the list.
    hosts = containers + inventory.get_hosts(host['hostname'])
    service_hosts = inventory.get_group(component + '_all').get_hosts()

    # Herer's the trick: intersection between node hosts and service hosts
    # (which include hosts from different nodes) gives ua only service
    # hosts on a given node.
    return list(set(hosts) & set(service_hosts))


class Driver(base.UpgradeDriver):
    """Upgrade driver implementation for OpenStack Ansible.

    As any upgrade driver returns a Celery task to be executed in order to
    achieve some goal (start upgrade, stop upgrade, etc). In order to have
    a successful execution it's mandatory to run those tasks on deployment
    host, so make sure you run your Celery worker there.

    Since OpenStack Ansible Newton we have the 'openstack-ansible.rc' shell
    script that must be sourced before running OpenStack Ansible and defines
    some Ansible env variables such as path to inventory. In order to avoid
    unnecessary complications in driver and to support as many versions as
    possible, it's up to end user to ensure that Celery worker is running
    with those env variables.

    There's another important note, hostnames in Kostyor's database must
    be the same used by OpenStack Ansible. So far we don't support
    mapping by IP address or something like that.
    """

    #: Kostyor is designed to have an upgrade resolution up to microservice.
    #: Unfortunately, OpenStack Ansible provides a resolution up to service,
    #: so technically we have the very same playbook for the whole list of
    #: service's subservices.
    _playbooks = {
        'keystone-wsgi-admin':       'os-keystone-install.yml',
        'keystone-wsgi-public':      'os-keystone-install.yml',

        'glance-api':                'os-glance-install.yml',
        'glance-registry':           'os-glance-install.yml',

        'nova-conductor':            'os-nova-install.yml',
        'nova-scheduler':            'os-nova-install.yml',
        'nova-cells':                'os-nova-install.yml',
        'nova-cert':                 'os-nova-install.yml',
        'nova-console':              'os-nova-install.yml',
        'nova-consoleauth':          'os-nova-install.yml',
        'nova-network':              'os-nova-install.yml',
        'nova-novncproxy':           'os-nova-install.yml',
        'nova-serialproxy':          'os-nova-install.yml',
        'nova-spicehtml5proxy':      'os-nova-install.yml',
        'nova-xvpvncproxy':          'os-nova-install.yml',
        'nova-api':                  'os-nova-install.yml',
        'nova-api-metadata':         'os-nova-install.yml',
        'nova-api-os-compute':       'os-nova-install.yml',
        'nova-compute':              'os-nova-install.yml',

        'neutron-server':            'os-neutron-install.yml',
        'neutron-openvswitch-agent': 'os-neutron-install.yml',
        'neutron-linuxbridge-agent': 'os-neutron-install.yml',
        'neutron-sriov-nic-agent':   'os-neutron-install.yml',
        'neutron-l3-agent':          'os-neutron-install.yml',
        'neutron-dhcp-agent':        'os-neutron-install.yml',
        'neutron-metering-agent':    'os-neutron-install.yml',
        'neutron-metadata-agent':    'os-neutron-install.yml',
        'neutron-ns-metadata-proxy': 'os-neutron-install.yml',

        'cinder-api':                'os-cinder-install.yml',
        'cinder-scheduler':          'os-cinder-install.yml',
        'cinder-volume':             'os-cinder-install.yml',

        'horizon-wsgi':              'os-horizon-install.yml',

        'heat-api':                  'os-heat-install.yml',
        'heat-engine':               'os-heat-install.yml',
        'heat-api-cfn':              'os-heat-install.yml',
        'heat-api-cloudwatch':       'os-heat-install.yml',

        'ceilometer-collector':             'os-ceilometer-install.yml',
        'ceilometer-agent-notification':    'os-ceilometer-install.yml',
        'ceilometer-polling':               'os-ceilometer-install.yml',
        'ceilometer-api':                   'os-ceilometer-install.yml',

        'aodh-evaluator':   'os-aodh-install.yml',
        'aodh-notifier':    'os-aodh-install.yml',
        'aodh-listener':    'os-aodh-install.yml',
        'aodh-api':         'os-aodh-install.yml',

        'gnocchi-statsd':   'os-gnocchi-install.yml',
        'gnocchi-metricd':  'os-gnocchi-install.yml',
        'gnocchi-api':      'os-gnocchi-install.yml',

        'swift-proxy-server':           'os-swift-install.yml',
        'swift-account-auditor':        'os-swift-install.yml',
        'swift-account-reaper':         'os-swift-install.yml',
        'swift-account-replicator':     'os-swift-install.yml',
        'swift-account-server':         'os-swift-install.yml',
        'swift-account-server':         'os-swift-install.yml',
        'swift-container-auditor':      'os-swift-install.yml',
        'swift-container-reconciler':   'os-swift-install.yml',
        'swift-container-replicator':   'os-swift-install.yml',
        'swift-container-server':       'os-swift-install.yml',
        'swift-container-sync':         'os-swift-install.yml',
        'swift-container-updater':      'os-swift-install.yml',
        'swift-object-auditor':         'os-swift-install.yml',
        'swift-object-expirer':         'os-swift-install.yml',
        'swift-object-reconstructor':   'os-swift-install.yml',
        'swift-object-replicator':      'os-swift-install.yml',
        'swift-object-server':          'os-swift-install.yml',
        'swift-object-server':          'os-swift-install.yml',
        'swift-object-updater':         'os-swift-install.yml',

        'ironic-inspector':     'os-ironic-install.yml',
        'ironic-conductor':     'os-ironic-install.yml',
        'ironic-api':           'os-ironic-install.yml',
    }

    # A path to OpenStack Ansible sources.
    #
    # TODO: to be configurable
    _root = os.path.join('/opt', 'openstack-ansible')

    _run_playbook = None
    _run_playbook_for = None

    def __init__(self, *args, **kwargs):
        super(Driver, self).__init__(*args, **kwargs)

        #: Due to the fact that we have one playbook that upgrades the whole
        #: service (multiple microservices at once), we will upgrade them all
        #: on the same host when firing, for instance, nova-api. In order
        #: to prevent running this playbook once again (it makes no sense),
        #: we need to track playbook executions per host.
        #:
        #: The dict has the following format:
        #:
        #:   (host, playbook) -> is-executed
        self._executions = {}

    def pre_upgrade_hook(self, upgrade_task):
        utilities = os.path.join(
            self._root, 'scripts', 'upgrade-utilities', 'playbooks')
        playbooks = os.path.join(self._root, 'playbooks')

        # According to the upgrade document, there are steps that must be
        # executed before trying to upgrade OpenStack to new version. This
        # this hook returns a chain of this steps so operator doesn't need
        # to run them manually.
        #
        # http://docs.openstack.org/developer/openstack-ansible/upgrade-guide/manual-upgrade.html
        return celery.chain(*[

            # Bootstrapping Ansible again ensures that all OpenStack Ansible
            # role dependencies are in place before running playbooks of new
            # release.
            tasks.execute.si(
                os.path.join(self._root, 'scripts', 'bootstrap-ansible.sh'),
                cwd=self._root,
            ),

            # Some configuration may changed, and old facts should be purged.
            self._run_playbook.si(
                os.path.join(utilities, 'ansible_fact_cleanup.yml'),
            ),

            # The user configuration files in /etc/openstack_deploy/ and
            # the environment layout in /etc/openstack_deploy/env.d may
            # have new name values added in new release.
            self._run_playbook.si(
                os.path.join(utilities, 'deploy-config-changes.yml'),
            ),

            # Populate user_secrets.yml with new secrets added in new
            # release.
            self._run_playbook.si(
                os.path.join(utilities, 'user-secrets-adjustment.yml'),
            ),

            # The presence of pip.conf file can cause build failures when
            # upgrading. So better remove it everywhere.
            self._run_playbook.si(
                os.path.join(utilities, 'pip-conf-removal.yml'),
            ),

            # Update the configuration of the repo servers and build a new
            # packages required by new release.
            self._run_playbook.si(
                os.path.join(playbooks, 'repo-install.yml'),
                cwd=playbooks,
            ),
        ])

    def start_upgrade(self, upgrade_task, service):
        # Kostyor's model may contain information about more services
        # than we support. It seems reasonable to do not fail on such
        # services and skip it for now.
        if service['name'] not in self._playbooks:
            return tasks.noop.si()

        # If playbook was executed on the host, then do nothing since.
        # This is a general case for this driver as long as one playbook
        # upgrades the whole service at once.
        key = service['host_id'], self._playbooks[service['name']]
        if self._executions.get(key):
            return tasks.noop.si()
        self._executions[key] = True

        return self._run_playbook_for.si(
            os.path.join(
                self._root, 'playbooks', self._playbooks[service['name']]
            ),

            # By default, OpenStack Ansible deploys control plane services
            # in LXC containers, and use those as hosts in Ansible inventory.
            # However, from Kostyor's point of view we are interested in
            # baremetal node-by-node upgrade and we don't want to know about
            # containers. So we need to limit playbook execution only to
            # a baremetal node and its containers.
            dbapi.get_host(service['host_id']),
            service,
        )

    def stop_upgrade(self, upgrade_task, service):
        raise NotImplementedError()

    def pause_upgrade(self, upgrade_task, service):
        raise NotImplementedError()

    def continue_upgrade(self, upgrade_task, service):
        raise NotImplementedError()

    def cancel_upgrade(self, upgrade_task, service):
        raise NotImplementedError()

    def rollback_upgrade(self, upgrade_task, service):
        raise NotImplementedError()

    def supports_upgrade_rollback(self):
        return False
