#
# sambacc: a samba container configuration tool
# Copyright (C) 2021  John Mulligan
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import os
import subprocess
import typing

from sambacc import config
from sambacc import samba_cmds
from sambacc.netcmd_loader import template_config


DB_DIR = "/var/lib/ctdb/persistent"


def ensure_smb_conf(
    iconfig: config.InstanceConfig, path: str = config.SMB_CONF
) -> None:
    """Ensure that the smb.conf on disk is ctdb and registry enabled."""
    with open(path, "w") as fh:
        write_smb_conf(fh, iconfig)


def write_smb_conf(fh: typing.IO, iconfig: config.InstanceConfig) -> None:
    """Write an smb.conf style output enabling ctdb and samba registry."""
    template_config(fh, iconfig.ctdb_smb_config())


_SRC_TDB_FILES = [
    "account_policy.tdb",
    "group_mapping.tdb",
    "passdb.tdb",
    "secrets.tdb",
    "share_info.td",
    "winbindd_idmap.tdb",
]


def migrate_tdb(iconfig: config.InstanceConfig, dest_dir: str) -> None:
    """Migrate TDB files into CTDB."""
    # TODO: these paths should be based on our instance config, not hard coded
    tdb_locations = ["/var/lib/samba", "/var/lib/samba/private"]
    for tdbfile in _SRC_TDB_FILES:
        for parent in tdb_locations:
            tdb_path = os.path.join(parent, tdbfile)
            try:
                _convert_tdb_file(tdb_path, dest_dir)
            except FileNotFoundError:
                pass


def _convert_tdb_file(tdb_path: str, dest_dir: str) -> None:
    if not os.path.isfile(tdb_path):
        # TODO: would be better to parse the error from the command
        raise FileNotFoundError(tdb_path)
    opath = os.path.join(dest_dir, os.path.basename(tdb_path))
    cmd = samba_cmds.ltdbtool["convert", "-s0", tdb_path, opath]
    subprocess.check_call(list(cmd))
