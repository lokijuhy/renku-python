# -*- coding: utf-8 -*-
#
# Copyright 2017-2021 - Swiss Data Science Center (SDSC)
# A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
# Eidgenössische Technische Hochschule Zürich (ETHZ).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test ``save`` command."""

import os

from renku.cli import cli
from renku.core.metadata.repository import Repository
from tests.utils import format_result_exception, write_and_commit_file


def test_save_without_remote(runner, project, client, tmpdir_factory):
    """Test saving local changes."""
    with (client.path / "tracked").open("w") as fp:
        fp.write("tracked file")

    result = runner.invoke(cli, ["save", "-m", "save changes", "tracked"], catch_exceptions=False)
    assert 1 == result.exit_code
    assert "No remote has been set up" in result.output

    path = str(tmpdir_factory.mktemp("remote"))
    Repository().initialize(path, bare=True)

    result = runner.invoke(cli, ["save", "-d", path, "tracked"], catch_exceptions=False)

    assert 0 == result.exit_code, format_result_exception(result)
    assert "tracked" in result.output
    assert "Saved changes to: tracked" in client.repository.head.commit.message

    client.repository.remotes.remove("origin")


def test_save_with_remote(runner, project, client_with_remote, tmpdir_factory):
    """Test saving local changes."""
    with (client_with_remote.path / "tracked").open("w") as fp:
        fp.write("tracked file")

    result = runner.invoke(cli, ["save", "-m", "save changes", "tracked"], catch_exceptions=False)

    assert 0 == result.exit_code, format_result_exception(result)
    assert "tracked" in result.output
    assert "save changes" in client_with_remote.repository.head.commit.message


def test_save_with_merge_conflict(runner, project, client_with_remote, tmpdir_factory):
    """Test saving local changes."""
    client = client_with_remote
    with (client.path / "tracked").open("w") as fp:
        fp.write("tracked file")

    result = runner.invoke(cli, ["save", "-m", "save changes", "tracked"], catch_exceptions=False)

    assert 0 == result.exit_code, format_result_exception(result)
    assert "tracked" in result.output
    assert "save changes" in client.repository.head.commit.message

    with (client.path / "tracked").open("w") as fp:
        fp.write("local changes")
    client.repository.add(client.path / "tracked")
    client.repository.commit("amended commit", amend=True)

    with (client.path / "tracked").open("w") as fp:
        fp.write("new version")

    result = runner.invoke(cli, ["save", "-m", "save changes", "tracked"], input="n", catch_exceptions=False)

    assert 0 == result.exit_code, format_result_exception(result)
    assert "There were conflicts when updating the local data" in result.output
    assert "Successfully saved to remote branch" in result.output
    assert "save changes" in client.repository.head.commit.message


def test_save_with_staged(runner, project, client_with_remote, tmpdir_factory):
    """Test saving local changes."""
    client = client_with_remote

    write_and_commit_file(client.repository, client.path / "deleted", "deleted file")
    os.remove(client.path / "deleted")

    (client.path / "tracked").write_text("tracked file")

    (client.path / "untracked").write_text("untracked file")

    client.repository.add("tracked", "deleted")

    result = runner.invoke(cli, ["save", "-m", "save changes", "modified", "deleted"], catch_exceptions=False)

    assert 1 == result.exit_code
    assert "These files are in the git staging area, but " in result.output
    assert "tracked" in result.output
    assert "tracked" in [f.a_path for f in client.repository.staged_changes]
    assert "untracked" in client.repository.untracked_files

    result = runner.invoke(
        cli, ["save", "-m", "save changes", "tracked", "untracked", "deleted"], catch_exceptions=False
    )

    assert 0 == result.exit_code, format_result_exception(result)
    assert {"tracked", "untracked", "deleted"} == {f.a_path for f in client.repository.head.commit.get_changes()}
    assert not client.repository.is_dirty(untracked_files=True)
