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
"""Renku service fixtures for project management."""
import os
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

import pytest

from renku.core.metadata.repository import Repository
from renku.core.utils.os import normalize_to_ascii


@pytest.fixture
def project_metadata(project):
    """Create project with metadata."""
    name = Path(project).name
    metadata = {
        "project_id": uuid.uuid4().hex,
        "name": name,
        "slug": normalize_to_ascii(name),
        "fullname": "full project name",
        "email": "my@email.com",
        "owner": "me",
        "token": "awesome token",
        "git_url": "git@gitlab.com",
        "initialized": True,
    }

    yield project, metadata


@pytest.fixture(scope="module")
def it_git_access_token():
    """Returns a git access token for a testing run."""
    from tests.fixtures.config import IT_GIT_ACCESS_TOKEN

    return IT_GIT_ACCESS_TOKEN


@pytest.fixture(scope="module")
def it_remote_repo_url():
    """Returns a remote path to integration test repository."""
    from tests.fixtures.config import IT_REMOTE_REPO_URL

    return IT_REMOTE_REPO_URL


@pytest.fixture(scope="module")
def it_remote_public_repo_url():
    """Returns a remote path to a public integration test repository."""
    return "https://dev.renku.ch/gitlab/renku-python-integration-tests/no-renku"


@pytest.fixture(scope="function")
def it_remote_repo_url_temp_branch(it_remote_repo_url):
    """Returns a remote path to integration test repository."""

    with tempfile.TemporaryDirectory() as tempdir:
        # NOTE: create temporary branch and push it
        git_url = urlparse(it_remote_repo_url)

        url = "oauth2:{0}@{1}".format(os.getenv("IT_OAUTH_GIT_TOKEN"), git_url.netloc)
        git_url = git_url._replace(netloc=url).geturl()
        repo = Repository.clone_from(url=git_url, path=tempdir)
        origin = repo.remotes["origin"]
        branch_name = uuid.uuid4().hex
        branch = repo.branches.add(branch_name)
        repo.push(origin, branch, set_upstream=True)
        try:
            yield it_remote_repo_url, branch_name
        finally:
            # NOTE: delete remote branch
            repo.push(origin, branch, delete=True)
            repo.branches.remove(branch)


@pytest.fixture(scope="module")
def it_non_renku_repo_url():
    """Returns a remote path to integration test repository."""
    from tests.fixtures.config import IT_REMOTE_NON_RENKU_REPO_URL

    return IT_REMOTE_NON_RENKU_REPO_URL


@pytest.fixture(scope="module")
def it_no_commit_repo_url():
    """Returns a remote path to integration test repository."""
    from tests.fixtures.config import IT_REMOTE_NO_COMMITS_REPO_URL

    return IT_REMOTE_NO_COMMITS_REPO_URL


@pytest.fixture(scope="module")
def it_protected_repo_url():
    """Returns a protected repository url."""
    from tests.fixtures.config import IT_PROTECTED_REMOTE_REPO_URL

    return IT_PROTECTED_REMOTE_REPO_URL
