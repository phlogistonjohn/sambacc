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

import argparse

from sambacc import ctdb

from .cli import commands, Context


def _ctdb_migrate_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dest-dir",
        default=ctdb.DB_DIR,
        help=("Specify where CTDB database files will be written."),
    )


@commands.command(name="ctdb-migrate", arg_func=_ctdb_migrate_args)
def ctdb_migrate(ctx: Context) -> None:
    """Migrate standard samba databases to CTDB databases."""
    ctdb.migrate_tdb(ctx.instance_config, ctx.cli.dest_dir)
