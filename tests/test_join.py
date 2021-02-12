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

import json
import os
import pytest

import sambacc.join


@pytest.fixture(scope="function")
def testjoiner(tmp_path):
    data_path = tmp_path / "_samba"
    data_path.mkdir()

    fake_net = [
        "#!/bin/sh",
        f'echo "ARGS:" "$@" > {data_path}/log',
        f"cat >> {data_path}/log",
        f"if grep -q failme {data_path}/log ; then exit 1; fi",
    ]
    fake_net_script = data_path / "net.sh"
    with open(fake_net_script, "w") as fh:
        fh.write("\n".join(fake_net))
        fh.write("\n")
    os.chmod(fake_net_script, 0x0755)

    class TestJoiner(sambacc.join.Joiner):
        cmd_prefix = [fake_net_script, "ads"]
        path = tmp_path
        logpath = data_path / "log"

    return TestJoiner()


def test_no_sources(testjoiner):
    with pytest.raises(sambacc.join.JoinError):
        testjoiner.join()


def test_invalid_source_vals(testjoiner):
    with pytest.raises(ValueError):
        testjoiner.add_source("bob", 123)
    with pytest.raises(ValueError):
        testjoiner.add_source(sambacc.join.JoinBy.PASSWORD, 123)
    with pytest.raises(ValueError):
        testjoiner.add_source(sambacc.join.JoinBy.FILE, 123)


def test_join_password(testjoiner):
    testjoiner.add_source(
        sambacc.join.JoinBy.PASSWORD,
        sambacc.join.UserPass("bugs", "whatsupdoc"),
    )
    testjoiner.join()


def test_join_file(testjoiner):
    jpath1 = os.path.join(testjoiner.path, "join1.json")
    with open(jpath1, "w") as fh:
        json.dump({"username": "elmer", "password": "hunter2"}, fh)
    testjoiner.add_source(
        sambacc.join.JoinBy.FILE,
        jpath1,
    )
    testjoiner.join()


def test_join_missing_file(testjoiner):
    jpath1 = os.path.join(testjoiner.path, "nope.json")
    testjoiner.add_source(
        sambacc.join.JoinBy.FILE,
        jpath1,
    )
    with pytest.raises(sambacc.join.JoinError) as err:
        testjoiner.join()
    assert "not found" in str(err).lower()


def test_join_bad_file(testjoiner):
    jpath1 = os.path.join(testjoiner.path, "join1.json")
    testjoiner.add_source(
        sambacc.join.JoinBy.FILE,
        jpath1,
    )

    with open(jpath1, "w") as fh:
        json.dump({"acme": True}, fh)
    with pytest.raises(sambacc.join.JoinError):
        testjoiner.join()

    with open(jpath1, "w") as fh:
        json.dump({"username": None, "password": "hunter2"}, fh)
    with pytest.raises(sambacc.join.JoinError):
        testjoiner.join()

    with open(jpath1, "w") as fh:
        json.dump({"username": "elmer", "password": 123}, fh)
    with pytest.raises(sambacc.join.JoinError):
        testjoiner.join()


def test_join_multi_source(testjoiner):
    testjoiner.add_source(
        sambacc.join.JoinBy.PASSWORD,
        sambacc.join.UserPass("bugs", "whatsupdoc"),
    )
    jpath1 = os.path.join(testjoiner.path, "join1.json")
    with open(jpath1, "w") as fh:
        json.dump({"username": "elmer", "password": "hunter2"}, fh)
    testjoiner.add_source(
        sambacc.join.JoinBy.FILE,
        jpath1,
    )
    testjoiner.join()

    with open(testjoiner.logpath) as fh:
        lines = fh.readlines()
    assert lines[0].startswith("ARGS")
    assert "bugs" in lines[0]
    assert "whatsupdoc" in lines[1]


def test_join_multi_source_fail_first(testjoiner):
    testjoiner.add_source(
        sambacc.join.JoinBy.PASSWORD,
        sambacc.join.UserPass("bugs", "failme"),
    )
    jpath1 = os.path.join(testjoiner.path, "join1.json")
    with open(jpath1, "w") as fh:
        json.dump({"username": "elmer", "password": "hunter2"}, fh)
    testjoiner.add_source(
        sambacc.join.JoinBy.FILE,
        jpath1,
    )
    testjoiner.join()

    with open(testjoiner.logpath) as fh:
        lines = fh.readlines()
    assert lines[0].startswith("ARGS")
    assert "elmer" in lines[0]
    assert "hunter2" in lines[1]


def test_join_multi_source_fail_both(testjoiner):
    testjoiner.add_source(
        sambacc.join.JoinBy.PASSWORD,
        sambacc.join.UserPass("bugs", "failme"),
    )
    jpath1 = os.path.join(testjoiner.path, "join1.json")
    with open(jpath1, "w") as fh:
        json.dump({"username": "elmer", "password": "failme2"}, fh)
    testjoiner.add_source(
        sambacc.join.JoinBy.FILE,
        jpath1,
    )
    with pytest.raises(sambacc.join.JoinError) as err:
        testjoiner.join()
    assert err.match("2 join attempts")
    assert len(err.value.errors) == 2

    with open(testjoiner.logpath) as fh:
        lines = fh.readlines()
    assert lines[0].startswith("ARGS")
    assert "elmer" in lines[0]
    assert "failme2" in lines[1]


def test_join_prompt_fake(testjoiner):
    testjoiner.add_source(
        sambacc.join.JoinBy.INTERACTIVE,
        sambacc.join.UserPass("daffy"),
    )
    testjoiner.join()

    with open(testjoiner.logpath) as fh:
        lines = fh.readlines()

    assert lines[0].startswith("ARGS")
    assert "daffy" in lines[0]
    assert len(lines) == 1
