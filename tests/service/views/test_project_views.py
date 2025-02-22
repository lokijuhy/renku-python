# -*- coding: utf-8 -*-
#
# Copyright 2019-2021 - Swiss Data Science Center (SDSC)
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
"""Renku service project view tests."""
import json
import re

import portalocker
import pytest

from tests.utils import retry_failed


def assert_rpc_response(response, with_key="result"):
    """Check rpc result in response."""
    assert response and 200 == response.status_code

    response_text = re.sub(r"http\S+", "", json.dumps(response.json))
    assert with_key in response_text


@pytest.mark.service
@pytest.mark.integration
@retry_failed
def test_show_project_view(svc_client_with_repo):
    """Test show project metadata."""
    svc_client, headers, project_id, _ = svc_client_with_repo

    show_payload = {
        "project_id": project_id,
    }
    response = svc_client.post("/1.1/project.show", data=json.dumps(show_payload), headers=headers)

    assert response
    assert_rpc_response(response)

    assert {
        "id",
        "name",
        "description",
        "created",
        "creator",
        "agent",
        "custom_metadata",
        "template_info",
        "keywords",
    } == set(response.json["result"])


@pytest.mark.service
@pytest.mark.integration
@retry_failed
def test_edit_project_view(svc_client_with_repo):
    """Test editing project metadata."""
    svc_client, headers, project_id, _ = svc_client_with_repo

    edit_payload = {
        "project_id": project_id,
        "description": "my new title",
        "creator": {"name": "name123", "email": "name123@ethz.ch", "affiliation": "ethz"},
        "custom_metadata": {
            "@id": "http://example.com/metadata12",
            "@type": "https://schema.org/myType",
            "https://schema.org/property1": 1,
            "https://schema.org/property2": "test",
        },
    }
    response = svc_client.post("/1.1/project.edit", data=json.dumps(edit_payload), headers=headers)

    assert response
    assert_rpc_response(response)

    assert {"warning", "edited", "remote_branch"} == set(response.json["result"])
    assert {
        "description": "my new title",
        "creator": {"name": "name123", "email": "name123@ethz.ch", "affiliation": "ethz"},
        "custom_metadata": {
            "@id": "http://example.com/metadata12",
            "@type": "https://schema.org/myType",
            "https://schema.org/property1": 1,
            "https://schema.org/property2": "test",
        },
    } == response.json["result"]["edited"]


@pytest.mark.integration
@pytest.mark.service
@retry_failed
def test_remote_edit_view(svc_client, it_remote_repo_url, identity_headers):
    """Test creating a delayed edit."""
    response = svc_client.post(
        "/1.1/project.edit",
        data=json.dumps(dict(git_url=it_remote_repo_url, is_delayed=True)),
        headers=identity_headers,
    )

    assert 200 == response.status_code
    assert response.json["result"]["created_at"]
    assert response.json["result"]["job_id"]


@pytest.mark.integration
@pytest.mark.service
def test_get_lock_status_unlocked(svc_client_setup):
    """Test getting lock status for an unlocked project."""
    svc_client, headers, project_id, _, _ = svc_client_setup

    response = svc_client.get(
        "/1.1/project.lock_status", query_string={"project_id": project_id}, headers=headers, content_type="text/xml"
    )

    assert 200 == response.status_code
    assert {"locked"} == set(response.json["result"].keys())
    assert response.json["result"]["locked"] is False


@pytest.mark.integration
@pytest.mark.service
def test_get_lock_status_locked(svc_client_setup):
    """Test getting lock status for a locked project."""
    svc_client, headers, project_id, _, repository = svc_client_setup

    def mock_lock():
        return portalocker.Lock(f"{repository.path}.lock", flags=portalocker.LOCK_EX, timeout=0)

    with mock_lock():
        response = svc_client.get("/1.1/project.lock_status", query_string={"project_id": project_id}, headers=headers)

    assert 200 == response.status_code
    assert {"locked"} == set(response.json["result"].keys())
    assert response.json["result"]["locked"] is True


@pytest.mark.integration
@pytest.mark.service
@pytest.mark.parametrize("query_params", [{"project_id": "dummy"}, {"git_url": "https://example.com/repo.git"}])
def test_get_lock_status_for_project_not_in_cache(svc_client, identity_headers, query_params):
    """Test getting lock status for an unlocked project which is not cached."""
    response = svc_client.get("/1.1/project.lock_status", query_string=query_params, headers=identity_headers)

    assert 200 == response.status_code
    assert {"locked"} == set(response.json["result"].keys())
    assert response.json["result"]["locked"] is False
