#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) Copyright IBM Corp. 2023
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: local_request_queue
short_description: Create and remove the CICS local request queue
description:
  - Create and remove the L(local request queue,https://www.ibm.com/docs/en/cics-ts/latest?topic=sets-local-request-queue-data-set)
    data set used by a CICS® region.
  - Useful when provisioning or de-provisioning a CICS region.
  - Use the O(state) option to specify the intended state for the local
    request queue. For example, O(state=initial) will create a local
    request queue data set if it doesn't yet exist, or it will take an existing
    local request queue and empty it of all records.
author: Drew Hughes (@andrewhughes101)
version_added: 1.1.0-beta.2
options:
  space_primary:
    description:
      - The size of the local request queue data set's primary space allocation.
        Note, this is just the value; the unit is specified with O(space_type).
      - This option only takes effect when the local request queue is being created.
        If it already exists, it has no effect.
      - The local request queue data set's secondary space allocation is set to 1.
    type: int
    required: false
    default: 4
  space_type:
    description:
      - The unit portion of the local request queue data set size. Note, this is
        just the unit; the value is specified with O(space_primary).
      - This option only takes effect when the local request queue is being created.
        If it already exists, it has no effect.
      - The size can be specified in megabytes (V(M)), kilobytes (V(K)),
        records (V(REC)), cylinders (V(CYL)), or tracks (V(TRK)).
    required: false
    type: str
    choices:
      - M
      - K
      - REC
      - CYL
      - TRK
    default: M
  location:
    description:
      - The name of the local request queue data set, e.g.
        C(REGIONS.ABCD0001.DFHLCD).
    type: str
    required: true
  state:
    description:
      - The desired state for the local request queue, which the module will aim to
        achieve.
      - V(absent) will remove the local request queue data set entirely, if it
        already exists.
      - V(initial) will create the local request queue data set if it does not
        already exist, and empty it of all existing records.
    choices:
      - "initial"
      - "absent"
    required: true
    type: str
'''


EXAMPLES = r"""
- name: Initialize a local request queue
  ibm.ibm_zos_cics.local_request_queue:
    location: "REGIONS.ABCD0001.DFHLRQ"
    state: "initial"

- name: Initialize a large request queue
  ibm.ibm_zos_cics.local_request_queue:
    location: "REGIONS.ABCD0001.DFHLRQ"
    space_primary: 50
    space_type: "M"
    state: "initial"

- name: Delete local request queue
  ibm.ibm_zos_cics.local_request_queue:
    location: "REGIONS.ABCD0001.DFHLRQ"
    state: "absent"
"""


RETURN = r"""
changed:
  description: True if the state was changed, otherwise False.
  returned: always
  type: bool
failed:
  description: True if the query job failed, otherwise False.
  returned: always
  type: bool
start_state:
  description:
    - The state of the local request queue before the task runs.
  returned: always
  type: dict
  contains:
    vsam:
      description: True if the data set is a VSAM data set.
      returned: always
      type: bool
    exists:
      description: True if the local request queue data set exists.
      type: bool
      returned: always
end_state:
  description: The state of the local request queue at the end of the task.
  returned: always
  type: dict
  contains:
    vsam:
      description: True if the data set is a VSAM data set.
      returned: always
      type: bool
    exists:
      description: True if the local request queue data set exists.
      type: bool
      returned: always
executions:
  description: A list of program executions performed during the task.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: A human-readable name for the program execution.
      type: str
      returned: always
    rc:
      description: The return code for the program execution.
      type: int
      returned: always
    stdout:
      description: The standard out stream returned by the program execution.
      type: str
      returned: always
    stderr:
      description: The standard error stream returned from the program execution.
      type: str
      returned: always
"""


import traceback

ZOS_CICS_IMP_ERR = None
try:
    from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.dataset_utils import (
        _run_idcams, AnsibleDataSetModule)
    from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.local_request_queue import (
        _local_request_queue, _get_idcams_cmd_lrq)
    from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.local_request_queue import _local_request_queue_constants as lrq_constants
    from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.dataset_utils import _dataset_constants as ds_constants
except ImportError:
    ZOS_CICS_IMP_ERR = traceback.format_exc()


class AnsibleLocalRequestQueueModule(AnsibleDataSetModule):
    def __init__(self):
        super(AnsibleLocalRequestQueueModule, self).__init__()

    def init_argument_spec(self):  # type: () -> Dict
        arg_spec = super(AnsibleLocalRequestQueueModule, self).init_argument_spec()

        arg_spec[ds_constants["PRIMARY_SPACE_VALUE_ALIAS"]].update({
            "default": lrq_constants["PRIMARY_SPACE_VALUE_DEFAULT"],
        })
        arg_spec[ds_constants["PRIMARY_SPACE_UNIT_ALIAS"]].update({
            "default": lrq_constants["SPACE_UNIT_DEFAULT"],
        })
        arg_spec[ds_constants["TARGET_STATE_ALIAS"]].update({
            "choices": lrq_constants["TARGET_STATE_OPTIONS"],
        })

        return arg_spec

    def _get_data_set_object(self, size, result):
        return _local_request_queue(
            size=size,
            name=result.get(ds_constants["DATASET_LOCATION_ALIAS"]).upper(),
            state=result.get(ds_constants["TARGET_STATE_ALIAS"]),
            exists=False,
            vsam=False
        )

    def _get_arg_defs(self):
        arg_def = super(AnsibleLocalRequestQueueModule, self)._get_arg_defs()

        arg_def[ds_constants["PRIMARY_SPACE_VALUE_ALIAS"]].update({
            "default": lrq_constants["PRIMARY_SPACE_VALUE_DEFAULT"]
        })
        arg_def[ds_constants["PRIMARY_SPACE_UNIT_ALIAS"]].update({
            "default": lrq_constants["SPACE_UNIT_DEFAULT"]
        }),
        arg_def[ds_constants["TARGET_STATE_ALIAS"]].update({
            "choices": lrq_constants["TARGET_STATE_OPTIONS"]
        })

        return arg_def

    def create_dataset(self):
        create_cmd = _get_idcams_cmd_lrq(self.data_set_definition)

        idcams_executions = _run_idcams(
            cmd=create_cmd,
            name="Create local request queue data set",
            location=self.data_set_definition["name"],
            delete=False)
        self.executions = self.executions + idcams_executions

        self.result["changed"] = True

    def delete_data_set(self):
        if not self.data_set_definition["exists"]:
            self.result['end_state'] = {
                "exists": self.data_set_definition["exists"],
                "vsam": self.data_set_definition["vsam"]
            }
            self._exit()

        delete_cmd = '''
        DELETE {0}
        '''.format(self.data_set_definition["name"])

        idcams_executions = _run_idcams(
            cmd=delete_cmd,
            name="Removing local request queue data set",
            location=self.data_set_definition["name"],
            delete=True)
        self.executions = self.executions + idcams_executions
        self.result["changed"] = True


def main():
    AnsibleLocalRequestQueueModule().main()


if __name__ == '__main__':
    main()
