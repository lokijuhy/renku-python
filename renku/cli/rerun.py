# -*- coding: utf-8 -*-
#
# Copyright 2018-2021- Swiss Data Science Center (SDSC)
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
r"""Recreate files created by the "run" command.

Recreating files
~~~~~~~~~~~~~~~~

.. image:: ../_static/asciicasts/rerun.delay.gif
   :width: 850
   :alt: Rerun workflow

Assume you have run a step 2 that uses a stochastic algorithm, so each run
will be slightly different. The goal is to regenerate output ``C`` several
times to compare the output. In this situation it is not possible to simply
call :ref:`cli-update` since the input file ``A`` has not been modified
after the execution of step 2.

.. code-block:: text

    A-[step 1]-B-[step 2*]-C

Recreate a specific output file by running:

  .. code-block:: console

     $ renku rerun C

If you do not want step 1 to also be rerun, you can specify a starting point
using the ``--from`` parameter:

  .. code-block:: console

     $ renku rerun --from B C

Note that all other outputs of the executed workflow will be recreated as well.
If the output didn't change, it will be removed from git and re-added to ensure
that the re-execution is properly tracked.


.. cheatsheet::
   :group: Running
   :command: $ renku rerun <path>
   :description: Recreate the file(s) <path> by rerunning the commands that
                 created them.
   :extended:
"""

import click
from lazy_object_proxy import Proxy

from renku.cli.utils.callback import ClickCallback
from renku.cli.utils.plugins import available_workflow_providers
from renku.core import errors


@click.command()
@click.option("--dry-run", "-n", is_flag=True, default=False, help="Show a preview of plans that will be executed.")
@click.option(
    "--from",
    "sources",
    type=click.Path(exists=True, dir_okay=False),
    multiple=True,
    help="Start an execution from this file.",
)
@click.argument("paths", type=click.Path(exists=True, dir_okay=True), nargs=-1, required=True)
@click.option(
    "provider",
    "-p",
    "--provider",
    default="cwltool",
    show_default=True,
    type=click.Choice(Proxy(available_workflow_providers), case_sensitive=False),
    help="The workflow engine to use.",
)
@click.option(
    "config", "-c", "--config", metavar="<config file>", help="YAML file containing configuration for the provider."
)
def rerun(dry_run, sources, paths, provider, config):
    """Recreate files generated by a sequence of ``run`` commands."""
    from renku.core.commands.format.activity import tabulate_activities
    from renku.core.commands.rerun import rerun_command

    communicator = ClickCallback()

    try:
        result = (
            rerun_command()
            .with_communicator(communicator)
            .build()
            .execute(dry_run=dry_run, sources=sources, paths=paths, provider=provider, config=config)
        )
    except errors.NothingToExecuteError:
        exit(1)
    else:
        if dry_run:
            activities, modified_inputs = result.output
            click.echo(tabulate_activities(activities, modified_inputs))
