# -*- coding: utf-8 -*-
#
# Copyright 2018 - Swiss Data Science Center (SDSC)
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
"""Workflow operations."""

import os

import click
import yaml

from renku.models.cwl._ascwl import ascwl

from ._client import pass_local_client
from ._graph import Graph


@click.group()
def workflow():
    """Workflow operations."""


@workflow.command()
@click.option('--revision', default='HEAD')
@click.option(
    '-o',
    '--output-file',
    metavar='FILE',
    type=click.File('w'),
    default='-',
    help='Write workflow to the FILE.',
)
@click.argument('paths', type=click.Path(dir_okay=True), nargs=-1)
@pass_local_client
def create(client, output_file, revision, paths):
    """Create a workflow description for a file."""
    graph = Graph(client)
    paths = [graph.normalize_path(path) for path in paths]
    outputs = graph.build(paths=paths, revision=revision)

    output_file.write(
        yaml.dump(
            ascwl(
                graph.ascwl(outputs=outputs),
                filter=lambda _, x: x is not None and x != [],
                basedir=os.path.dirname(getattr(output_file, 'name', '.')) or
                '.',
            ),
            default_flow_style=False
        )
    )
