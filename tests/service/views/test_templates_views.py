# -*- coding: utf-8 -*-
#
# Copyright 2020-2021 - Swiss Data Science Center (SDSC)
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
"""Renku service templates view tests."""
import base64
import json
from copy import deepcopy
from io import BytesIO
from time import sleep

import pytest

from renku.core.management.template.template import fetch_templates_source
from renku.core.metadata.repository import Repository
from renku.core.models.template import TEMPLATE_MANIFEST, TemplatesManifest
from renku.core.utils.os import normalize_to_ascii
from renku.service.config import RENKU_EXCEPTION_ERROR_CODE
from tests.utils import retry_failed


@pytest.mark.service
@pytest.mark.integration
@retry_failed
def test_read_manifest_from_template(svc_client_with_templates):
    """Check reading manifest template."""
    from PIL import Image

    svc_client, headers, template_params = svc_client_with_templates

    response = svc_client.get("/templates.read_manifest", query_string=template_params, headers=headers)

    assert response
    assert {"result"} == set(response.json.keys())
    assert response.json["result"]["templates"]

    templates = response.json["result"]["templates"]
    assert len(templates) > 0

    default_template = templates[template_params["index"] - 1]
    assert default_template["folder"] == template_params["id"]
    assert "icon" in default_template and default_template["icon"]
    icon = Image.open(BytesIO(base64.b64decode(default_template["icon"])))
    assert icon.size == (256, 256)


@pytest.mark.service
@pytest.mark.integration
def test_compare_manifests(svc_client_with_templates):
    """Check reading manifest template."""
    svc_client, headers, template_params = svc_client_with_templates

    response = svc_client.get("/templates.read_manifest", query_string=template_params, headers=headers)

    assert response
    assert {"result"} == set(response.json.keys())
    assert response.json["result"]["templates"]

    templates_source = fetch_templates_source(source=template_params["url"], reference=template_params["ref"])
    manifest_file = templates_source.path / TEMPLATE_MANIFEST

    manifest = TemplatesManifest.from_path(manifest_file).get_raw_content()

    assert manifest_file and manifest_file.exists()
    assert manifest

    templates_service = response.json["result"]["templates"]
    templates_local = manifest
    default_index = template_params["index"] - 1

    if "icon" in templates_service[default_index]:
        del templates_service[default_index]["icon"]
    if "icon" in templates_local[default_index]:
        del templates_local[default_index]["icon"]

    assert templates_service[default_index] == templates_local[default_index]


@pytest.mark.service
@pytest.mark.integration
@retry_failed
def test_create_project_from_template(svc_client_templates_creation):
    """Check reading manifest template."""
    from renku.service.serializers.headers import RenkuHeaders
    from renku.service.utils import CACHE_PROJECTS_PATH

    svc_client, headers, payload, rm_remote = svc_client_templates_creation

    # NOTE:  fail: remote authentication
    anonymous_headers = deepcopy(headers)
    anonymous_headers["Authorization"] = "Bearer None"
    response = svc_client.post("/templates.create_project", data=json.dumps(payload), headers=anonymous_headers)

    assert response
    assert response.json.get("error") is not None, response.json
    assert "Cannot push changes" in response.json["error"]["reason"]

    # NOTE:  fail: missing parameters
    if len(payload["parameters"]) > 0:
        payload_without_parameters = deepcopy(payload)
        payload_without_parameters["parameters"] = []
        response = svc_client.post(
            "/templates.create_project", data=json.dumps(payload_without_parameters), headers=headers
        )
        assert response
        assert response.json["error"]
        assert RENKU_EXCEPTION_ERROR_CODE == response.json["error"]["code"]
        assert "missing parameter" in response.json["error"]["reason"]

    # NOTE:  successfully push with proper authentication
    response = svc_client.post("/templates.create_project", data=json.dumps(payload), headers=headers)

    assert response
    assert {"result"} == set(response.json.keys()), response.json["error"]
    stripped_name = normalize_to_ascii(payload["project_name"])
    assert stripped_name == response.json["result"]["slug"]
    expected_url = "{0}/{1}/{2}".format(payload["project_repository"], payload["project_namespace"], stripped_name)
    assert expected_url == response.json["result"]["url"]

    # NOTE: assert correct git user is set on new project
    user_data = RenkuHeaders.decode_user(headers["Renku-User"])
    project_path = (
        CACHE_PROJECTS_PATH
        / user_data["user_id"]
        / response.json["result"]["project_id"]
        / payload["project_namespace"]
        / stripped_name
    )
    reader = Repository(project_path).get_configuration()
    assert reader.get_value("user", "email") == user_data["email"]
    assert reader.get_value("user", "name") == user_data["name"]

    # NOTE:  successfully re-use old name after cleanup
    assert rm_remote() is True
    sleep(1)  # NOTE: sleep to make sure remote isn't locked
    response = svc_client.post("/templates.create_project", data=json.dumps(payload), headers=headers)
    assert response
    assert {"result"} == set(response.json.keys())
    assert expected_url == response.json["result"]["url"]
