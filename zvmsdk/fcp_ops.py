#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Reference implementation of the FCP operations.

``TransactionalFcpOperations`` runs each operation on an FCPDbOperatorBase
inside one transaction. It never calls z/VM, so a backend that serves
feilong from another process can reuse it with its own operator and
transaction.
"""

from zvmsdk import config
from zvmsdk import db_interface
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG

# positions in a zvm_fcps value, see FCP.to_tuple()
_ZVM_FCP_ID, _ZVM_NPIV, _ZVM_PHY, _ZVM_CHPID, _ZVM_PCHID, _ZVM_STATE, \
    _ZVM_OWNER = range(7)


def check_missing_pchids(db, fcp_template_id, pchid_info):
    """Raise if pchid_info lacks a PCHID used by the FCP template."""
    # uppercase the keys (PCHIDs) in pchid_info
    pchid_info = {pchid.upper(): pchid_info[pchid] for pchid in pchid_info}
    LOG.info("Get pchid_info: {} when allocating FCP devices from template: {}"
             .format(pchid_info, fcp_template_id))
    # verify pchid_info
    pchids_in_template = set(db.get_pchids_by_fcp_template(fcp_template_id))
    pchids_in_pchid_info = set(pchid_info)
    missing_pchids = sorted(list(pchids_in_template - pchids_in_pchid_info))
    if missing_pchids:
        errmsg = ('The PCHIDs configured in the FCP multipath template (id={}) are {}, '
                  'but the statistics of PCHIDs {} are missing.'
                  .format(fcp_template_id, sorted(list(pchids_in_template)), missing_pchids))
        LOG.error(errmsg)
        raise exception.SDKVolumeOperationError(rs=12, msg=errmsg)


def validate_fcp_wwpns(fcp_list, assigner_id):
    """Raise if wwpn_npiv or wwpn_phy of any FCP is empty."""
    for fcp in fcp_list:
        fcp_id, wwpn_npiv, wwpn_phy, *_ = fcp
        if not wwpn_npiv:
            # wwpn_npiv not found in FCP DB
            errmsg = ("NPIV WWPN of FCP device %s not found in "
                      "database." % fcp_id)
            LOG.error(errmsg)
            raise exception.SDKVolumeOperationError(rs=11,
                                                    userid=assigner_id,
                                                    msg=errmsg)
        # We use initiator to build up zones on fabric, for NPIV, the
        # virtual ports are not yet logged in when we creating zones.
        # so we will generate the physical virtual initiator mapping
        # to determine the proper zoning on the fabric.
        # Refer to #7039 for details about avoid creating zones on
        # the fabric to which there is no fcp connected.
        if not wwpn_phy:
            errmsg = ("Physical WWPN of FCP device %s not found in "
                      "database." % fcp[0])
            LOG.error(errmsg)
            raise exception.SDKVolumeOperationError(rs=11,
                                                    userid=assigner_id,
                                                    msg=errmsg)


class TransactionalFcpOperations(db_interface.FcpOperationsBase):
    """FCP operations on an FCPDbOperatorBase.

    :param db: the FCPDbOperatorBase to use.
    :param transaction: a callable returning a context manager that runs
        its body as one transaction and can be nested.
    """

    def __init__(self, db, transaction):
        self.db = db
        self._transaction = transaction

    def increase_connections(self, fcp_list, assigner_id):
        with self._transaction():
            fcp_connections = {}
            for fcp in fcp_list:
                # increase connections by 1
                fcp_connections[fcp] = self.db.increase_connections_by_assigner(fcp, assigner_id)
            return fcp_connections

    def decrease_connections(self, fcp_list):
        with self._transaction():
            fcp_connections = {}
            for fcp in fcp_list:
                try:
                    LOG.info('Decreasing the connections of FCP device {}'.format(fcp))
                    # Decrease connections of FCP device by 1
                    fcp_connections[fcp] = self.db.decrease_connections(fcp)
                except exception.SDKObjectNotExistError:
                    fcp_connections[fcp] = 0
            return fcp_connections

    def _check_template_exists(self, assigner_id, fcp_template_id):
        if fcp_template_id and not self.db.fcp_template_exist_in_db(fcp_template_id):
            errmsg = ("FCP Multipath Template (id: %s) does not exist." % fcp_template_id)
            LOG.error(errmsg)
            raise exception.SDKVolumeOperationError(
                rs=11, userid=assigner_id, msg=errmsg)

    def _get_default_template_id(self, assigner_id, sp_name):
        LOG.info("FCP Multipath Template id is not specified when reserving FCP "
                 "devices for assigner %s." % assigner_id)
        if sp_name:
            LOG.info("Get the default FCP Multipath Template id for Storage "
                     "Provider %s " % sp_name)
            default_tmpl = self.db.get_sp_default_fcp_template([sp_name])
        if not sp_name or not default_tmpl:
            LOG.info("Can not find the default FCP Multipath Template id for "
                     "storage provider %s. Get the host default FCP "
                     "template id for assigner %s" % (sp_name,
                                                      assigner_id))
            default_tmpl = self.db.get_host_default_fcp_template()
        if not default_tmpl:
            errmsg = ("No FCP Multipath Template is specified and "
                      "no default FCP Multipath Template is found.")
            LOG.error(errmsg)
            raise exception.SDKVolumeOperationError(rs=11,
                                                    userid=assigner_id,
                                                    msg=errmsg)
        fcp_template_id = default_tmpl[0]['id']
        LOG.info("The default FCP Multipath Template id is %s." % fcp_template_id)
        return fcp_template_id

    def allocate(self, assigner_id, fcp_template_id, sp_name, pchid_info,
                 zvm_fcps=None):
        is_reserved_changed = False
        with self._transaction():
            self._check_template_exists(assigner_id, fcp_template_id)
            # try getting a default template if no specified template
            if not fcp_template_id:
                fcp_template_id = self._get_default_template_id(assigner_id, sp_name)

            try:
                # get the FCP devices allocated to the userid if any
                fcp_list = self.db.get_allocated_fcps_from_assigner(
                    assigner_id, fcp_template_id)
                LOG.info("Previously allocated FCP devices %s for "
                         "instance %s in FCP Multipath Template %s." %
                         ([f['fcp_id'] for f in fcp_list],
                          assigner_id, fcp_template_id))
                empty_fcp_list_reason = ''
                if not fcp_list:
                    # Check whether all the PCHIDs used by the FCP multipath template is contained in
                    # the pchid_info
                    check_missing_pchids(self.db, fcp_template_id, pchid_info)
                    if zvm_fcps is None:
                        # allocating new FCPs must be based on the latest FCP state
                        return db_interface.NEED_ZVM_SYNC, fcp_template_id
                    # Sync DB to update FCP state,
                    # so that allocating new FCPs is based on the latest FCP state
                    self.sync_with_zvm(zvm_fcps)
                    # allocate new ones if fcp_list is empty
                    LOG.info("There is no previously allocated FCP devices for the instance %s, "
                             "allocating new ones." % assigner_id)
                    if CONF.volume.get_fcp_pair_with_same_index:
                        # If use get_fcp_pair_with_same_index,
                        # then FCP devices are randomly selected from below combinations,
                        # one FCP device per path, ex:
                        # [fa00,fb00],[fa01,fb01],[fa02,fb02]
                        fcp_list, empty_fcp_list_reason = self.db.get_fcp_devices_with_same_index(
                            fcp_template_id, pchid_info)
                    else:
                        # If use get_fcp_pair,
                        # then FCP devices are randomly selected from below combinations,
                        # one FCP device per path, ex:
                        # [fa00,fb00],[fa01,fb00],[fa02,fb00]
                        # [fa00,fb01],[fa01,fb01],[fa02,fb01]
                        # [fa00,fb02],[fa01,fb02],[fa02,fb02]
                        fcp_list, empty_fcp_list_reason = self.db.get_fcp_devices(
                            fcp_template_id, pchid_info)
                    # process empty fcp_list
                    if not fcp_list:
                        return is_reserved_changed, [], fcp_template_id, empty_fcp_list_reason
                    # record the assigner id in the fcp DB so that
                    # when the vm provision with both root and data volumes
                    # the root and data volume would get the same FCP devices
                    # with the get_volume_connector call.
                    fcp_ids = [fcp['fcp_id'] for fcp in fcp_list]
                    assigner_id = assigner_id.upper()
                    self.db.reserve_fcps(fcp_ids, assigner_id, fcp_template_id)
                    is_reserved_changed = True
                    LOG.info("Newly allocated %s FCP devices for instance %s "
                             "and FCP Multipath Template %s" %
                             (fcp_ids, assigner_id, fcp_template_id))
                else:
                    # reuse the old ones if fcp_list is not empty
                    LOG.info("Found previously allocated FCP devices %s "
                             "for instance %s in FCP Multipath Template %s, "
                             "will reuse them."
                             % ([f['fcp_id'] for f in fcp_list],
                                assigner_id, fcp_template_id))
                    path_count = self.db.get_path_count(fcp_template_id)
                    if len(fcp_list) != path_count:
                        LOG.warning("FCP devices previously allocated to instance %s are %s, "
                                    "it is not equal to the total path count (%s) "
                                    "of the FCP Multipath Template." %
                                    (assigner_id, fcp_list, path_count))
                    validate_fcp_wwpns(fcp_list, assigner_id)
                # return
                return is_reserved_changed, fcp_list, fcp_template_id, empty_fcp_list_reason
            except Exception as err:
                errmsg = ("Failed to reserve FCP devices "
                          "for assigner %s by FCP Multipath Template %s error: %s"
                          % (assigner_id, fcp_template_id, err.message))
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)

    def release(self, assigner_id, fcp_template_id):
        is_reserved_changed = False
        fcp_ids = []
        with self._transaction():
            self._check_template_exists(assigner_id, fcp_template_id)
            try:
                if fcp_template_id is None:
                    errmsg = ("fcp_template_id is not specified "
                              "while releasing FCP devices.")
                    LOG.error(errmsg)
                    raise exception.SDKVolumeOperationError(rs=11,
                                                            userid=assigner_id,
                                                            msg=errmsg)
                fcp_list = self.db.get_reserved_fcps_from_assigner(
                    assigner_id, fcp_template_id)
                if fcp_list:
                    validate_fcp_wwpns(fcp_list, assigner_id)
                    # the data structure of fcp_list is
                    # [(fcp_id, wwpn_npiv, wwpn_phy, connections, path, pchid)]
                    # only unreserve the fcp with connections=0
                    fcp_ids = [fcp['fcp_id'] for fcp in fcp_list
                               if fcp['connections'] == 0]
                    if fcp_ids:
                        self.db.unreserve_fcps(fcp_ids)
                        is_reserved_changed = True
                        LOG.info("Unreserve fcp device %s from "
                                 "instance %s and FCP Multipath Template %s."
                                 % (fcp_ids, assigner_id, fcp_template_id))
            except Exception as err:
                errmsg = ("Failed to unreserve FCP devices for "
                          "assigner %s by FCP Multipath Template %s. Error: %s"
                          % (assigner_id, fcp_template_id, err.message))
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)
        return is_reserved_changed, fcp_list or [], fcp_ids

    def _get_fcp_dict_in_db(self):
        try:
            # Get all FCPs found in DB.
            fcp_in_db = self.db.get_all_fcps_of_assigner()
        except exception.SDKObjectNotExistError:
            fcp_in_db = list()
            # no record in db is normal during sync,
            # such as when there is no fcp_list configured
            LOG.warning("No fcp records found in database and ignore "
                        "the exception.")
        return {fcp['fcp_id'].lower(): fcp for fcp in fcp_in_db}

    def sync_with_zvm(self, zvm_fcps):
        """Update FCP records queried from zVM into FCP table."""
        # copy, as in-use FCPs get their DB WWPNs written back below
        zvm_fcps = {fcp: list(info) for fcp, info in zvm_fcps.items()}
        with self._transaction():
            # Get a dict of all FCPs already existed in FCP table
            fcp_dict_in_db = self._get_fcp_dict_in_db()
            # Divide FCPs into three sets
            inter_set = set(zvm_fcps) & set(fcp_dict_in_db)
            del_fcp_set = set(fcp_dict_in_db) - inter_set
            add_fcp_set = set(zvm_fcps) - inter_set

            # Add new records into FCP table
            fcp_info_need_insert = [tuple(zvm_fcps[fcp])
                                    for fcp in add_fcp_set]
            LOG.info("New FCP devices found on z/VM: {}".format(add_fcp_set))
            self.db.bulk_insert_zvm_fcp_info_into_fcp_table(
                fcp_info_need_insert)

            # Delete FCP records from FCP table
            # if it is connections=0 and reserve=0
            LOG.info("FCP devices exist in FCP table but not in "
                     "z/VM any more: {}".format(del_fcp_set))
            fcp_ids_secure_to_delete = set()
            fcp_ids_not_found = set()
            for fcp in del_fcp_set:
                # example of a FCP record in fcp_dict_in_db
                # (fcp_id, userid, connections, reserved, wwpn_npiv,
                #  wwpn_phy, chpid, pchid, state, owner, tmpl_id)
                (fcp_id, userid, connections, reserved, wwpn_npiv_db,
                 wwpn_phy_db, chpid_db, pchid_db, fcp_state_db,
                 fcp_owner_db, tmpl_id) = fcp_dict_in_db[fcp]
                if connections == 0 and reserved == 0:
                    fcp_ids_secure_to_delete.add(fcp)
                else:
                    # these records not found in z/VM
                    # but still in-use in FCP table
                    fcp_ids_not_found.add(fcp)
            self.db.bulk_delete_from_fcp_table(
                fcp_ids_secure_to_delete)
            LOG.info("FCP devices removed from FCP table: {}".format(
                fcp_ids_secure_to_delete))
            # For records not found in ZVM, but still in-use in DB
            # mark them as not found
            if fcp_ids_not_found:
                self.db.bulk_update_state_in_fcp_table(fcp_ids_not_found,
                                                       'notfound')
                LOG.info("Ignore the request of deleting in-use "
                         "FCPs: {}.".format(fcp_ids_not_found))

            # Update status for FCP records already existed in DB
            LOG.info("FCP devices exist in both FCP table and "
                     "z/VM: {}".format(inter_set))
            fcp_ids_need_update = set()
            for fcp in inter_set:
                # example of a FCP record in fcp_dict_in_db
                # (fcp_id, userid, connections, reserved, wwpn_npiv,
                #  wwpn_phy, chpid, pchid, state, owner, tmpl_id)
                (fcp_id, userid, connections, reserved, wwpn_npiv_db,
                 wwpn_phy_db, chpid_db, pchid_db, fcp_state_db,
                 fcp_owner_db, tmpl_id) = fcp_dict_in_db[fcp]
                zvm_fcp = zvm_fcps[fcp]
                # Possible state returned by ZVM:
                # 'active', 'free' or 'offline'
                # Possible FCP owner returned by ZVM:
                # VM userid: if the FCP is attached to a VM
                # A String "NONE": if the FCP is not attached
                # Check WWPNs need update or not
                if wwpn_npiv_db == '' or (connections == 0 and reserved == 0):
                    # The WWPNs are secure to be updated when:
                    # case1(wwpn_npiv_db == ''): the wwpn_npiv_db is empty, for example, upgraded from 114.
                    # case2(connections == 0 and reserved == 0): the FCP device is not in use.
                    if (wwpn_npiv_db != zvm_fcp[_ZVM_NPIV] or
                            wwpn_phy_db != zvm_fcp[_ZVM_PHY]):
                        # only need to update wwpns when they are different
                        fcp_ids_need_update.add(fcp)
                else:
                    # For an in-used FCP device, even its WWPNs are changed in z/VM,
                    # we can NOT update the wwpn_npiv, wwpn_phy columns in FCP DB because the host mapping from
                    # storage provider backend is still using the old WWPNs recorded in FCP DB.
                    # To detach the volume and delete the host mapping successfully, we need make sure the WWPNs records
                    # in FCP DB unchanged in this case.
                    # Because all z/VM properties are written to DB when any of them changes,
                    # keep the DB WWPNs in the z/VM record so that they are not changed.
                    zvm_fcp[_ZVM_NPIV] = wwpn_npiv_db
                    zvm_fcp[_ZVM_PHY] = wwpn_phy_db
                # Other cases need to update FCP record in DB
                if chpid_db != zvm_fcp[_ZVM_CHPID]:
                    # Check chpid changed or not
                    fcp_ids_need_update.add(fcp)
                elif pchid_db != zvm_fcp[_ZVM_PCHID]:
                    # Check pchid changed or not
                    fcp_ids_need_update.add(fcp)
                elif fcp_state_db != zvm_fcp[_ZVM_STATE]:
                    # Check state changed or not
                    fcp_ids_need_update.add(fcp)
                elif fcp_owner_db != zvm_fcp[_ZVM_OWNER]:
                    # Check owner changed or not
                    fcp_ids_need_update.add(fcp)
                else:
                    LOG.debug("No need to update record of FCP "
                              "device {}".format(fcp))
            fcp_info_need_update = [tuple(zvm_fcps[fcp])
                                    for fcp in fcp_ids_need_update]
            self.db.bulk_update_zvm_fcp_info_in_fcp_table(fcp_info_need_update)
            LOG.info("FCP devices need to update records in "
                     "fcp table: {}".format(fcp_info_need_update))

    def get_pchid_usage(self):
        with self._transaction():
            all_pchids = self.db.get_pchids_from_all_fcp_templates()
            inuse_pchids = self.db.get_pchids_of_all_inuse_fcp_devices()
        return all_pchids, inuse_pchids
