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
"""Template view model."""

from typing import Any, Dict, List, Optional

from renku.core.management.template.template import FileAction, RenderedTemplate, get_sorted_actions
from renku.core.models.template import Template, TemplateParameter
from renku.core.utils.util import to_string


class TemplateViewModel:
    """A view model for a ``Template``."""

    def __init__(
        self,
        description: str,
        icon: Optional[str],
        id: str,
        immutable_files: Optional[List],
        name: str,
        reference: Optional[str],
        source: str,
        parameters: List[TemplateParameter],
        version: str,
        versions: List[str],
    ):
        self.description: str = description
        self.icon = icon
        self.id: str = id
        self.immutable_files: List[str] = immutable_files
        self.name: str = name
        self.reference = reference
        self.source = source
        self.parameters: List[TemplateParameterViewModel] = [
            TemplateParameterViewModel.from_template_parameter(p) for p in parameters
        ]
        self.version = version
        self.versions = versions

    @classmethod
    def from_template(cls, template: Template) -> "TemplateViewModel":
        """Create view model from ``Template``."""
        return cls(
            source=template.source,
            reference=template.reference,
            version=template.version,
            id=template.id,
            name=template.name,
            description=template.description,
            parameters=template.parameters,
            icon=template.icon,
            immutable_files=template.immutable_files,
            versions=template.get_all_versions(),
        )


class TemplateParameterViewModel:
    """A view model for a ``TemplateParameter``."""

    def __init__(
        self,
        name: str,
        description: str,
        type: str,
        possible_values: List[str],
        default: str,
    ):
        self.name: str = name
        self.description: str = description
        self.type: str = type
        self.possible_values: List[Any] = possible_values
        self.default: Optional[str] = default

    @classmethod
    def from_template_parameter(cls, parameter: TemplateParameter) -> "TemplateParameterViewModel":
        """Create view model from ``Template``."""
        return cls(
            name=parameter.name,
            description=parameter.description,
            type=to_string(parameter.type),
            possible_values=parameter.possible_values or [],
            default=parameter.default,
        )


class TemplateChangeViewModel:
    """A view model for resulting changes from a template set/update."""

    def __init__(self, id: str, source: str, reference: Optional[str], version: str, file_changes: List[str]):
        self.id: str = id
        self.source = source
        self.reference = reference
        self.version = version
        self.file_changes = file_changes

    @classmethod
    def from_template(cls, template: RenderedTemplate, actions: Dict[str, FileAction]) -> "TemplateChangeViewModel":
        """Create view model from ``Template``."""
        actions_mapping: Dict[FileAction, str] = {
            FileAction.APPEND: "Append to",
            FileAction.CREATE: "Initialize",
            FileAction.DELETED: "Ignore deleted file",
            FileAction.IGNORE_IDENTICAL: "Ignore unchanged file",
            FileAction.IGNORE_UNCHANGED_REMOTE: "Ignore unchanged template file",
            FileAction.KEEP: "Keep",
            FileAction.OVERWRITE: "Overwrite",
            FileAction.RECREATE: "Recreate deleted file",
        }

        file_changes = [
            f"{actions_mapping[action]} {relative_path} ..."
            for relative_path, action in get_sorted_actions(actions=actions).items()
        ]

        return cls(
            id=template.template.id,
            source=template.template.source,
            reference=template.template.reference,
            version=template.template.version,
            file_changes=file_changes,
        )
