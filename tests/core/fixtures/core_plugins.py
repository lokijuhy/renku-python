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
"""Renku core fixtures for plugins testing."""
from pathlib import Path
from typing import Optional

import pytest

from renku.core.models.workflow.converters import IWorkflowConverter
from renku.core.models.workflow.plan import Plan


@pytest.fixture
def dummy_run_plugin_hook():
    """A dummy hook to be used with the renku run plugin."""
    from renku.core.plugins import hookimpl

    class _CmdlineToolAnnotations(object):
        """CmdlineTool Hook implementation namespace."""

        @hookimpl
        def cmdline_tool_annotations(self, tool):
            """``cmdline_tool_annotations`` hook implementation."""
            from renku.core.models.provenance.annotation import Annotation

            return [Annotation(id="_:annotation", source="Dummy Cmdline Hook", body="dummy cmdline hook body")]

    return _CmdlineToolAnnotations()


@pytest.fixture
def dummy_pre_run_plugin_hook():
    """A dummy hook to be used with the renku run plugin."""
    from renku.core.plugins import hookimpl

    class _PreRun(object):
        """CmdlineTool Hook implementation namespace."""

        called = 0

        @hookimpl
        def pre_run(self, tool):
            """``cmdline_tool_annotations`` hook implementation."""
            self.called = 1

    return _PreRun()


@pytest.fixture
def dummy_processrun_plugin_hook():
    """A dummy hook to be used with the renku run plugin."""
    from renku.core.plugins import hookimpl

    class _ActivityAnnotations(object):
        """CmdlineTool Hook implementation namespace."""

        @hookimpl
        def process_run_annotations(self, plan):
            """``process_run_annotations`` hook implementation."""
            from renku.core.models.provenance.annotation import Annotation

            return [Annotation(id="_:annotation", source="Dummy Activity Hook", body="dummy Activity hook body")]

    return _ActivityAnnotations()


@pytest.fixture
def dummy_workflow_exporter_hook():
    """A dummy hook to be used with the renku run plugin."""
    from renku.core.plugins import hookimpl

    class DummyWorkflowExporter(IWorkflowConverter):
        """CmdlineTool Hook implementation namespace."""

        @hookimpl
        def workflow_format(self):
            return (self, ["dummy"])

        @hookimpl
        def workflow_convert(
            self, workflow: Plan, basedir: Path, output: Optional[Path], output_format: Optional[str]
        ) -> str:
            return "dummy"

    return DummyWorkflowExporter()
