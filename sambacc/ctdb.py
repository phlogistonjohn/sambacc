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

import typing

from sambacc import config
from sambacc.netcmd_loader import template_config


def ensure_smb_conf(
    iconfig: config.InstanceConfig, path: str = config.SMB_CONF
) -> None:
    """Ensure that the smb.conf on disk is ctdb and registry enabled."""
    with open(path, "w") as fh:
        write_smb_conf(fh, iconfig)


def write_smb_conf(fh: typing.IO, iconfig: config.InstanceConfig) -> None:
    """Write an smb.conf style output enabling ctdb and samba registry."""
    template_config(fh, iconfig.ctdb_smb_config())


def migrate_tdb(iconfig: config.InstanceConfig) -> None:
    """Migrate TDB files into CTDB."""
    pass  # TODO
