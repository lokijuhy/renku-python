# -*- coding: utf-8 -*-
#
# Copyright 2021 Swiss Data Science Center (SDSC)
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
"""Renku fixtures for repository management."""
import contextlib
import os
import secrets
import shutil

import pytest

from renku.core.management.client import LocalClient
from renku.core.metadata.repository import Repository
from tests.utils import format_result_exception


@contextlib.contextmanager
def _isolated_filesystem(tmpdir, name=None, delete=True):
    """Click CliRunner ``isolated_filesystem`` but xdist compatible."""
    from renku.core.utils.contexts import chdir

    if not name:
        name = secrets.token_hex(8)
    t = tmpdir.mkdir(name)

    with chdir(t):
        try:
            yield t
        finally:
            if delete:
                try:
                    shutil.rmtree(t)
                except OSError:  # noqa: B014
                    pass


@pytest.fixture()
def renku_path(tmpdir):
    """Temporary instance path."""
    path = str(tmpdir.mkdir("renku"))
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def instance_path(renku_path, monkeypatch):
    """Temporary instance path."""
    with monkeypatch.context() as m:
        m.chdir(renku_path)
        yield renku_path


@pytest.fixture
def repository(tmpdir):
    """Yield a Renku repository."""
    from click.testing import CliRunner

    from renku.cli import cli

    runner = CliRunner()
    with _isolated_filesystem(tmpdir, delete=True) as project_path:
        home = tmpdir.mkdir("user_home")
        old_home = os.environ.get("HOME", "")
        old_xdg_home = os.environ.get("XDG_CONFIG_HOME", "")

        try:
            # NOTE: fake user home directory
            os.environ["HOME"] = str(home)
            os.environ["XDG_CONFIG_HOME"] = str(home)
            with Repository.get_global_configuration(writable=True) as global_config:
                global_config.set_value("user", "name", "Renku @ SDSC")
                global_config.set_value("user", "email", "renku@datascience.ch")
                global_config.set_value("pull", "rebase", "false")

            result = runner.invoke(cli, ["init", ".", "--template-id", "python-minimal"], "\n", catch_exceptions=False)
            assert 0 == result.exit_code, format_result_exception(result)

            yield os.path.realpath(project_path)
        finally:
            os.environ["HOME"] = old_home
            os.environ["XDG_CONFIG_HOME"] = old_xdg_home
            try:
                shutil.rmtree(home)
            except OSError:  # noqa: B014
                pass


@pytest.fixture
def project(repository):
    """Create a test project."""
    from click.testing import CliRunner

    from renku.cli import cli
    from renku.core.utils.contexts import chdir

    runner = CliRunner()

    repo = Repository(repository, search_parent_directories=True)
    commit = repo.head.commit

    with chdir(repository):
        yield repository

        os.chdir(repository)
        repo.reset(commit, hard=True)
        # INFO: remove any extra non-tracked files (.pyc, etc)
        repo.clean()
        assert 0 == runner.invoke(cli, ["githooks", "install", "--force"]).exit_code


@pytest.fixture
def client(project, global_config_dir) -> LocalClient:
    """Return a Renku repository."""
    from renku.core.models.enums import ConfigFilter

    original_get_value = LocalClient.get_value

    def mocked_get_value(self, section, key, config_filter=ConfigFilter.ALL):
        """We don't want lfs warnings in tests."""
        if key == "show_lfs_message":
            return "False"
        return original_get_value(self, section, key, config_filter=config_filter)

    LocalClient.get_value = mocked_get_value

    yield LocalClient(path=project)

    LocalClient.get_value = original_get_value


@pytest.fixture
def client_injection_bindings():
    """Return bindings needed for client dependency injection."""

    def _create_client_bindings(client):
        from renku.core.management.command_builder.client_dispatcher import ClientDispatcher
        from renku.core.management.interface.client_dispatcher import IClientDispatcher

        client_dispatcher = ClientDispatcher()
        client_dispatcher.push_created_client_to_stack(client)
        return {"bindings": {"LocalClient": client, IClientDispatcher: client_dispatcher}, "constructor_bindings": {}}

    return _create_client_bindings


@pytest.fixture
def injection_binder(request):
    """Return a binder that can work with bindings."""

    def _binder(bindings):
        from renku.core.management.command_builder.command import inject, remove_injector

        def _bind(binder):
            for key, value in bindings["bindings"].items():
                binder.bind(key, value)
            for key, value in bindings["constructor_bindings"].items():
                binder.bind_to_constructor(key, value)

            return binder

        inject.configure(_bind, bind_in_runtime=False)
        request.addfinalizer(lambda: remove_injector())
        return

    return _binder
