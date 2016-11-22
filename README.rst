================================
Kostyor OpenStack Ansible Driver
================================

`Kostyor`_ is a deployment agnostic upgrade service for `OpenStack`_, and
this is a Kostyor driver that supports `OpenStack Ansible`_ deployments.

Want to try?

.. code:: bash

    $ [sudo] python -m pip install kostyor-openstack-ansible


Prerequirements
===============

#. Celery worker that's going to execute OpenStack Ansible playbooks must
   run on the deployment host.

#. Celery worker that's going to execute OpenStack Ansible playbooks must
   have defined environment variables from ``openstack-ansible.rc``.

   In other words, if you run manually you've got to do:

   .. code:: bash

      # source /usr/local/bin/openstack-ansible.rc
      # celery -A kostyor.rpc.app worker

#. Celery worker that's going to execute OpenStack Ansible playbooks must
   have installed Ansible in its environment. One may consider to use
   a virtualenv created by OpenStack Ansible - ``/opt/ansible-runtime``.

#. Celery worker that's going to execute OpenStack Ansible playbooks must
   be ran from ``root``. Superuser privileges may not work.


Links
=====

* Documentation: https://kostyor-openstack-ansible.readthedocs.org/
* Source: https://github.com/ikalnytskyi/kostyor-openstack-ansible
* Bugs: https://github.com/ikalnytskyi/kostyor-openstack-ansible/issues

.. _Kostyor: https://github.com/sc68cal/Kostyor
.. _OpenStack: https://www.openstack.org
.. _OpenStack Ansible: http://docs.openstack.org/developer/openstack-ansible/
