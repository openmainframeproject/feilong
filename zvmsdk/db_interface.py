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

"""Interfaces for pluggable database backends.

Feilong reaches its database only through the operator objects returned by
a ``DbBackend`` (see ``zvmsdk.database.get_db_backend``). The SQLite classes
in ``zvmsdk.database`` are the reference implementation; a backend selected
with ``[database] backend`` must behave the same way:

* Signatures, arguments and return shapes match the SQLite classes.
* Rows are ``sqlite3.Row``-compatible: accessible by column index, by
  column name and by unpacking. Backends that do not return ``sqlite3.Row``
  can use ``DbRow``.
* Errors are raised as the existing feilong exceptions (for example
  ``SDKObjectNotExistError``, ``SDKNetworkOperationError``,
  ``SDKGuestOperationError``, ``SDKDatabaseException``), so callers need no
  changes.
"""

import abc
import collections.abc


class DbRow(collections.abc.Sequence):
    """A read-only row with ``sqlite3.Row`` style access.

    Supports ``row[0]``, ``row['col']``, ``len(row)``, iteration over the
    values, unpacking, ``row.keys()`` and ``dict(row)``.
    """

    __slots__ = ('_keys', '_values', '_index')

    def __init__(self, keys, values):
        keys = tuple(keys)
        values = tuple(values)
        if len(keys) != len(values):
            raise ValueError('DbRow got %d keys and %d values'
                             % (len(keys), len(values)))
        self._keys = keys
        self._values = values
        # sqlite3.Row matches names case-insensitively, first column wins
        self._index = {}
        for i, k in enumerate(keys):
            self._index.setdefault(k.lower(), i)

    @classmethod
    def from_dict(cls, data):
        return cls(data.keys(), data.values())

    def keys(self):
        return list(self._keys)

    def __getitem__(self, item):
        if isinstance(item, str):
            try:
                return self._values[self._index[item.lower()]]
            except KeyError:
                raise IndexError('No item with that key')
        return self._values[item]

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def __eq__(self, other):
        if isinstance(other, DbRow):
            return (self._keys == other._keys and
                    self._values == other._values)
        return NotImplemented

    def __hash__(self):
        return hash((self._keys, self._values))

    def __repr__(self):
        return 'DbRow(%r)' % dict(zip(self._keys, self._values))


class NetworkDbOperatorBase(abc.ABC):
    """Operations on the ``switch`` data.

    Switch records are returned as a list of dicts with the keys
    ``userid``, ``interface``, ``switch``, ``port`` and ``comments``.
    """

    @abc.abstractmethod
    def switch_delete_record_for_userid(self, userid):
        """Delete all switch records of userid. Returns None."""

    @abc.abstractmethod
    def switch_delete_record_for_nic(self, userid, interface):
        """Delete the switch record of userid/interface. Returns None."""

    @abc.abstractmethod
    def switch_add_record(self, userid, interface, port=None,
                          switch=None, comments=None):
        """Add a switch record. Returns None."""

    @abc.abstractmethod
    def switch_add_record_migrated(self, userid, interface, switch,
                                   port=None, comments=None):
        """Add a switch record for a migrated guest. Returns None."""

    @abc.abstractmethod
    def switch_update_record_with_switch(self, userid, interface,
                                         switch=None):
        """Set (or clear when None) the switch of userid/interface.

        Raises SDKObjectNotExistError if the record does not exist.
        """

    @abc.abstractmethod
    def switch_select_table(self):
        """Return all switch records."""

    @abc.abstractmethod
    def switch_select_record_for_userid(self, userid):
        """Return the switch records of userid."""

    @abc.abstractmethod
    def switch_select_record(self, userid=None, nic_id=None, vswitch=None):
        """Return the switch records matching all given filters.

        nic_id matches the ``port`` column. With no filter, returns all.
        """


class ImageDbOperatorBase(abc.ABC):
    """Operations on the ``image`` data."""

    @abc.abstractmethod
    def image_add_record(self, imagename, imageosdistro, checksum,
                         disk_size_units, image_size_in_bytes,
                         type, comments=None):
        """Add an image record. Returns None."""

    @abc.abstractmethod
    def image_query_record(self, imagename=None):
        """Return image records as a list of dicts.

        Keys: imagename, imageosdistro, checksum, disk_size_units,
        image_size_in_bytes, type, comments. With imagename, raises
        SDKObjectNotExistError if it does not exist; without, returns all.
        """

    @abc.abstractmethod
    def image_delete_record(self, imagename):
        """Delete the image record. Returns None."""


class GuestDbOperatorBase(abc.ABC):
    """Operations on the ``guests`` data.

    Guest rows have the columns (id, userid, metadata, net_set, comments).
    """

    @abc.abstractmethod
    def add_guest_registered(self, userid, meta, net_set, comments=None):
        """Add a migrated or onboarded guest with a new UUID."""

    @abc.abstractmethod
    def add_guest(self, userid, meta='', comments=''):
        """Add a guest with a new UUID and net_set '0'."""

    @abc.abstractmethod
    def delete_guest_by_id(self, guest_id):
        """Delete the guest; a missing guest is ignored."""

    @abc.abstractmethod
    def delete_guest_by_userid(self, userid):
        """Delete the guest; a missing guest is ignored."""

    @abc.abstractmethod
    def get_guest_metadata_with_userid(self, userid):
        """Return a list of (metadata,) rows for userid."""

    @abc.abstractmethod
    def update_guest_by_id(self, uuid, userid=None, meta=None, net_set=None,
                           comments=None):
        """Update the given fields; comments are stored as given.

        Raises SDKInternalError if no field is given and
        SDKObjectNotExistError if the guest does not exist.
        """

    @abc.abstractmethod
    def update_guest_by_userid(self, userid, meta=None, net_set=None,
                               comments=None):
        """Update the given fields; comments are stored JSON-encoded.

        Raises SDKInternalError if no field is given and
        SDKObjectNotExistError if the guest does not exist.
        """

    @abc.abstractmethod
    def get_guest_list(self):
        """Return all guest rows."""

    @abc.abstractmethod
    def get_migrated_guest_list(self):
        """Return (userid,) rows of guests whose comments mark them
        migrated (``"migrated": 1``)."""

    @abc.abstractmethod
    def get_migrated_guest_info_list(self):
        """Return guest rows of guests whose comments mark them migrated."""

    @abc.abstractmethod
    def get_comments_by_userid(self, userid):
        """Return the decoded comments dict ({} when empty)."""

    @abc.abstractmethod
    def get_metadata_by_userid(self, userid):
        """Return the metadata string ('' if the guest does not exist)."""

    def transfer_metadata_to_dict(self, meta):
        """Turn "a=1,b=2" into {'a': '1', 'b': '2'}."""
        dic = {}
        arr = meta.strip(' ,').split(',')
        for i in arr:
            temp = i.split('=')
            dic[temp[0].strip()] = temp[1].strip()
        return dic

    @abc.abstractmethod
    def get_guest_by_id(self, guest_id):
        """Return the guest row, or None."""

    @abc.abstractmethod
    def get_guest_by_userid(self, userid):
        """Return the guest row, or None."""


class FCPDbOperatorBase(abc.ABC):
    """Operations on the FCP data: tables ``fcp``, ``template``,
    ``template_sp_mapping`` and ``template_fcp_mapping``.

    Rows must support access by column name. See the docstrings of
    ``zvmsdk.database.FCPDbOperator`` for full examples.
    """

    # fcp table
    @abc.abstractmethod
    def unreserve_fcps(self, fcp_ids):
        """Set reserved=0 and tmpl_id='' for the FCPs."""

    @abc.abstractmethod
    def reserve_fcps(self, fcp_ids, assigner_id, fcp_template_id):
        """Set reserved=1, assigner_id and tmpl_id for the FCPs."""

    @abc.abstractmethod
    def bulk_insert_zvm_fcp_info_into_fcp_table(self, fcp_info_list):
        """Insert (fcp_id, wwpn_npiv, wwpn_phy, chpid, pchid, state, owner)
        tuples."""

    @abc.abstractmethod
    def bulk_delete_from_fcp_table(self, fcp_id_list):
        """Delete the FCP records."""

    @abc.abstractmethod
    def bulk_update_zvm_fcp_info_in_fcp_table(self, fcp_info_list):
        """Update from (fcp_id, wwpn_npiv, wwpn_phy, chpid, pchid, state,
        owner) tuples."""

    @abc.abstractmethod
    def bulk_update_state_in_fcp_table(self, fcp_id_list, new_state,
                                       new_owner=None):
        """Set state, and owner unless new_owner is None, for the FCPs."""

    @abc.abstractmethod
    def reset_fcps_of_assigner(self, userid):
        """Clear assigner_id, reserved, connections and tmpl_id of the
        assigner's FCPs; an FCP 'active' for the assigner becomes
        'free'/'none'. Returns the number of FCPs reset."""

    @abc.abstractmethod
    def get_all_fcps_of_assigner(self, assigner_id=None):
        """Return rows (fcp_id, assigner_id, connections, reserved,
        wwpn_npiv, wwpn_phy, chpid, pchid, state, owner, tmpl_id) of the
        assigner, or of all FCPs. Raises SDKObjectNotExistError if none."""

    @abc.abstractmethod
    def get_usage_of_fcp(self, fcp_id):
        """Return (assigner_id, reserved, connections, tmpl_id).

        Raises SDKObjectNotExistError if the FCP does not exist.
        """

    @abc.abstractmethod
    def update_usage_of_fcp(self, fcp, assigner_id, reserved, connections,
                            fcp_template_id):
        """Set assigner_id, reserved, connections and tmpl_id."""

    @abc.abstractmethod
    def increase_connections_by_assigner(self, fcp, assigner_id):
        """Increment connections and return the new count.

        Raises SDKObjectNotExistError if fcp is not assigned to assigner_id.
        """

    @abc.abstractmethod
    def decrease_connections(self, fcp):
        """Decrement connections and return the new count.

        Raises SDKObjectNotExistError if the FCP does not exist or already
        has 0 connections.
        """

    @abc.abstractmethod
    def get_connections_from_fcp(self, fcp):
        """Return connections. Raises SDKObjectNotExistError if missing."""

    @abc.abstractmethod
    def get_all(self):
        """Return rows of all FCPs, same columns as
        get_all_fcps_of_assigner."""

    @abc.abstractmethod
    def get_inuse_fcp_device_by_fcp_template(self, fcp_template_id):
        """Return (fcp_id,) rows of FCPs whose fcp.tmpl_id matches."""

    # template_fcp_mapping table
    @abc.abstractmethod
    def update_path_of_fcp_device(self, record):
        """Update path from a (path, fcp_id, fcp_template_id) tuple."""

    @abc.abstractmethod
    def get_path_count(self, fcp_template_id):
        """Return the number of distinct paths of the template."""

    @abc.abstractmethod
    def bulk_delete_fcp_device_from_fcp_template(self, records):
        """Delete (fcp_template_id, fcp_id) mappings."""

    @abc.abstractmethod
    def bulk_insert_fcp_device_into_fcp_template(self, records):
        """Insert (fcp_template_id, fcp_id, path) mappings."""

    # template table
    @abc.abstractmethod
    def fcp_template_exist_in_db(self, fcp_template_id):
        """Return True if the template exists."""

    @abc.abstractmethod
    def get_min_fcp_paths_count_from_db(self, fcp_template_id):
        """Return the stored min_fcp_paths_count, or None if no template."""

    @abc.abstractmethod
    def update_basic_info_of_fcp_template(self, record):
        """Update from a (name, description, host_default,
        min_fcp_paths_count, fcp_template_id) tuple; host_default=True
        clears is_default on all other templates."""

    # template_sp_mapping table
    @abc.abstractmethod
    def sp_name_exist_in_db(self, sp_name):
        """Return True if the storage provider has a default template."""

    @abc.abstractmethod
    def bulk_set_sp_default_by_fcp_template(self, template_id,
                                            sp_name_list):
        """Make template_id the only default of exactly sp_name_list."""

    # multiple tables
    @abc.abstractmethod
    def get_allocated_fcps_from_assigner(self, assigner_id,
                                         fcp_template_id):
        """Return rows (fcp_id, wwpn_npiv, wwpn_phy, path, pchid) with
        connections<>0 or reserved<>0, ordered by fcp_id."""

    @abc.abstractmethod
    def get_reserved_fcps_from_assigner(self, assigner_id, fcp_template_id):
        """Return rows (fcp_id, wwpn_npiv, wwpn_phy, connections, path,
        pchid) with reserved<>0, ordered by fcp_id."""

    @abc.abstractmethod
    def get_fcp_devices_with_same_index(self, fcp_template_id, pchid_info):
        """Return (fcp_list, empty_fcp_list_reason) picking free FCPs with
        the same index on every path."""

    @abc.abstractmethod
    def get_fcp_devices(self, fcp_template_id, pchid_info):
        """Return (fcp_list, empty_fcp_list_reason) picking one free FCP
        per path, honouring min_fcp_paths_count."""

    @abc.abstractmethod
    def create_fcp_template(self, fcp_template_id, name, description,
                            fcp_devices_by_path, host_default,
                            default_sp_list, min_fcp_paths_count=None):
        """Create a template with its FCP and SP mappings. Returns None.

        Raises SDKObjectAlreadyExistError if fcp_template_id exists.
        """

    @abc.abstractmethod
    def get_min_fcp_paths_count(self, fcp_template_id):
        """Return min_fcp_paths_count, or the path count when it is -1.

        Raises SDKObjectNotExistError if the template does not exist.
        """

    @abc.abstractmethod
    def edit_fcp_template(self, fcp_template_id, name=None,
                          description=None, fcp_devices=None,
                          host_default=None, default_sp_list=None,
                          min_fcp_paths_count=None):
        """Update the given fields and return {'fcp_template': {...}}
        (see FCPDbOperator.edit_fcp_template).

        Raises SDKObjectNotExistError if the template does not exist and
        SDKConflictError if an in-use FCP would be removed or moved.
        """

    @abc.abstractmethod
    def get_pchids_from_all_fcp_templates(self):
        """Return the list of PCHIDs used by any template."""

    @abc.abstractmethod
    def get_pchids_of_all_inuse_fcp_devices(self):
        """Return {pchid: 'fcp ranges'} of FCPs allocated from templates."""

    @abc.abstractmethod
    def get_fcp_templates(self, template_id_list=None):
        """Return rows (id, name, description, is_default,
        min_fcp_paths_count, sp_name) of the templates, or of all."""

    @abc.abstractmethod
    def get_pchids_by_fcp_template(self, fcp_template_id):
        """Return the list of PCHIDs of the template."""

    @abc.abstractmethod
    def get_free_pchids_by_fcp_template(self, fcp_template_id):
        """Return {path: [pchid, ...]} of PCHIDs with free FCPs."""

    @abc.abstractmethod
    def get_host_default_fcp_template(self, host_default=True):
        """Return template rows (as get_fcp_templates) with the given
        is_default."""

    @abc.abstractmethod
    def get_sp_default_fcp_template(self, sp_host_list):
        """Return template rows (as get_fcp_templates) that are default
        for the storage providers ('all' for every SP)."""

    @abc.abstractmethod
    def get_fcp_template_by_assigner_id(self, assigner_id):
        """Return template rows (as get_fcp_templates) the assigner's
        FCPs belong to."""

    @abc.abstractmethod
    def get_fcp_templates_details(self, template_id_list=None):
        """Return (template_rows, device_rows); see
        FCPDbOperator.get_fcp_templates_details for the columns."""

    @abc.abstractmethod
    def bulk_delete_fcp_from_template(self, fcp_id_list, fcp_template_id):
        """Remove FCPs from the template, skipping any that are in use
        (connections<>0 or reserved<>0)."""

    @abc.abstractmethod
    def delete_fcp_template(self, template_id):
        """Delete the template and its mappings. Raises
        SDKObjectNotExistError if missing, SDKConflictError if in use."""

    @abc.abstractmethod
    def get_wwpn_phy_from_pchids(self, pchids):
        """Return {pchid: wwpn_phy}."""


# Returned by FcpOperationsBase.allocate when the caller must query z/VM.
NEED_ZVM_SYNC = 'NEED_ZVM_SYNC'


class FcpOperationsBase(abc.ABC):
    """FCP operations that span several FCP DB calls.

    Each operation is atomic: it runs as one transaction in the backend,
    and the z/VM state it needs is passed in by the caller. ``zvm_fcps``
    is a dict keyed by lowercase FCP ID whose values are
    (fcp_id, wwpn_npiv, wwpn_phy, chpid, pchid, state, owner) sequences,
    as returned by ``volumeop.FCP.to_tuple()``.

    The reference implementation is ``zvmsdk.fcp_ops.TransactionalFcpOperations``.
    """

    @abc.abstractmethod
    def increase_connections(self, fcp_list, assigner_id):
        """Increment connections of each FCP; return {fcp: connections}."""

    @abc.abstractmethod
    def decrease_connections(self, fcp_list):
        """Decrement connections of each FCP; return {fcp: connections}.

        An FCP that does not exist or has no connections maps to 0.
        """

    @abc.abstractmethod
    def allocate(self, assigner_id, fcp_template_id, sp_name, pchid_info,
                 zvm_fcps=None):
        """Return the FCPs allocated to the assigner, reserving new ones
        if it has none.

        Raises SDKVolumeOperationError (rs=11) if fcp_template_id is given
        but does not exist, or if it is not given and no SP or host
        default template exists.

        If the assigner already has FCPs, returns
        (False, fcp_list, fcp_template_id, ''). Otherwise, when zvm_fcps
        is None, changes nothing and returns
        (NEED_ZVM_SYNC, fcp_template_id) with the resolved template ID;
        the caller then queries z/VM and calls again with zvm_fcps and that
        template ID. With zvm_fcps, syncs the fcp table, picks and reserves
        new FCPs and returns (True, fcp_list, fcp_template_id, '') or
        (False, [], fcp_template_id, empty_fcp_list_reason).
        """

    @abc.abstractmethod
    def release(self, assigner_id, fcp_template_id):
        """Unreserve the assigner's reserved FCPs that have no connections.

        Returns (is_reserved_changed, fcp_list, released_fcp_ids), where
        fcp_list holds all reserved FCPs of the assigner in the template.
        The caller syncs the fcp table with z/VM if released_fcp_ids is
        not empty.
        """

    @abc.abstractmethod
    def sync_with_zvm(self, zvm_fcps):
        """Bring the fcp table in line with the FCPs found on z/VM."""

    @abc.abstractmethod
    def get_pchid_usage(self):
        """Return (all_pchids, inuse_pchids) from one consistent read.

        See FCPDbOperatorBase.get_pchids_from_all_fcp_templates and
        get_pchids_of_all_inuse_fcp_devices.
        """


class DbBackend(abc.ABC):
    """Factory of the operator objects for one database backend.

    Each call may return a new operator or a shared one; operators must be
    safe to use from multiple threads.
    """

    @abc.abstractmethod
    def network(self):
        """Return a NetworkDbOperatorBase."""

    @abc.abstractmethod
    def guest(self):
        """Return a GuestDbOperatorBase."""

    @abc.abstractmethod
    def image(self):
        """Return an ImageDbOperatorBase."""

    @abc.abstractmethod
    def fcp(self):
        """Return an FCPDbOperatorBase."""

    @abc.abstractmethod
    def fcp_ops(self):
        """Return an FcpOperationsBase."""
