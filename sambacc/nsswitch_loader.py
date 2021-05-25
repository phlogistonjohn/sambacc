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

from .textfile import TextFileLoader


class NameServiceSwitchLoader(TextFileLoader):
    def __init__(self, path):
        super().__init__(path)
        self.lines = []
        self.idx = {}

    def loadlines(self, lines: typing.Iterable[str]) -> None:
        """Load in the lines from the text source."""
        # Ignore comments and blank lines
        for line in lines:
            if not line.strip() or line.startswith("#"):
                continue
            self.lines.append(line)
        for lnum, line in enumerate(self.lines):
            if line.startswith("passwd:"):
                self.idx["passwd"] = lnum
            if line.startswith("group:"):
                self.idx["group"] = lnum

    def dumplines(self) -> typing.Iterable[str]:
        """Dump the file content as lines of text."""
        prev = None
        yield "# Generated by sambacc -- DO NOT EDIT\n"
        for line in self.lines:
            if prev and not prev.endswith("\n"):
                yield "\n"
            yield line
            prev = line

    def winbind_enabled(self) -> bool:
        pline = self.lines[self.idx["passwd"]]
        gline = self.lines[self.idx["group"]]
        return ("winbind" in pline) and ("winbind" in gline)

    def ensure_winbind_enabled(self) -> None:
        pidx = self.idx["passwd"]
        if "winbind" not in self.lines[pidx]:
            self.lines[pidx] = "passwd:    files winbind\n"
        gidx = self.idx["group"]
        if "winbind" not in self.lines[gidx]:
            self.lines[gidx] = "group:    files winbind\n"
