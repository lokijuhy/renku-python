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
"""Manage the set of CWL files created by ``renku`` commands.

Manipulating workflows
~~~~~~~~~~~~~~~~~~~~~~

Listing workflows:

.. code-block:: console

    $ renku workflow ls
    26be2e8d66f74130a087642768f2cef0_rerun.yaml:
    199c4b9d462f4b27a4513e5e55f76eb2_cat.yaml:
    9bea2eccf9624de387d9b06e61eec0b6_rerun.yaml:
    b681b4e229764ceda161f6551370af12_update.yaml:
    25d0805243e3468d92a3786df782a2c4_rerun.yaml:

Each ``*.yaml`` file corresponds to a renku run/update/rerun execution.

Exporting workflows:

You can export the workflow to create a file as Common Workflow Language
by using:

.. code-block:: console

    $ renku workflow set-name create output_file
    baseCommand:
    - cat
    class: CommandLineTool
    cwlVersion: v1.0
    id: 22943eca-fa4c-4f3b-a92d-f6ac7badc0d2
    inputs:
    - default:
        class: File
        path: /home/user/project/intermediate
    id: inputs_1
    inputBinding:
        position: 1
    type: File
    - default:
        class: File
        path: /home/user/project/intermediate2
    id: inputs_2
    inputBinding:
        position: 2
    type: File
    outputs:
    - id: output_stdout
    streamable: false
    type: stdout
    requirements:
    InitialWorkDirRequirement:
        listing:
        - entry: $(inputs.inputs_1)
        entryname: intermediate
        writable: false
        - entry: $(inputs.inputs_2)
        entryname: intermediate2
        writable: false
    stdout: output_file

You can use ``--revision`` to specify the revision of the output file to
generate the workflow for. You can also export to a file directly with
``-o <path>``.


Composing workflows into larger workflows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more complex workflows consisting of several steps, you can use the
``renku workflow group`` command. This creates a new workflow that has
substeps.

The basic usage is:

.. code-block:: console

   $ renku run --name step1 -- command
   $ renku run --name step2 -- command
   $ renku workflow group my-grouped-workflow step1 step2

This would create a new workflow ``my-grouped-workflow`` that consists
of ``step1`` and ``step2`` as steps. This new workflow is just
like any other workflow in renku in that it can be executed, exported
or grouped with other workflows.

You can expose parameters of child steps on the parent workflow using
``--map``/``-m``  arguments followed by a mapping expression. Mapping expressions
take the form of ``<name>=<expression>`` where ``name`` is the name of the
property to be created on the parent workflow and expression points to one
or more fields on the child steps that should be mapped to this property.
The expressions come in two flavors, absolute references using the names
of workflows and properties, and relative references specifying the
position within a workflow.

An absolute expression in the example above could be ``step1.my_dataset``
to refer to the input, output or argument named ``my_dataset` on the step
``step1``. A relative expression could be ``@step2.@output1`` to refer
to the first output of the second step of the grouped workflow.

Valid relative expressions are ``@input<n>``, ``@output<n>`` and ``@param<n>``
for the n'th input, output or argument of a step, respectively. For referring
to steps inside a grouped workflow, you can use ``@step<n>``. For referencing
a mapping on a grouped workflow, you can use ``@mapping<n>``. Of course, the
names of the objects for all these cases also work.

The expressions can also be combined using ``,`` if a mapping should point
to more than one parameter of a child step.

You can mix absolute and relative reference in the same expression, as you see fit.

A full example of this would be:

.. code-block:: console

   $ renku workflow group --map input_file=step1.@input2 \
       --map output_file=@step1.my-output,@step2.step2s_output \
       my-grouped-workflow step1 step2

This would create a mapping called ``input_file`` on the parent workflow that
points to the second input of ``step1`` and a mapping called ``output_file``
that points to both the output ``my-output`` on ``step1`` and
``step2s_output`` on ``step2``.

You can also set default values for mappings, which override the default values
of the parameters they're pointing to by using the ``--set``/``-s`` parameter, for
instance:

.. code-block:: console

   $ renku workflow group --map input_file=step1.@input2 \
       --set input_file=data.csv
       my-grouped-workflow step1 step2


This would lead to ``data.csv`` being used for the second input of
``step1`` when ``my-grouped-workflow`` is executed (if it isn't overridden
at execution time).

You can add a description to the mappings to make them more human-readable
by using the ``--describe-param``/``-p`` parameter, as shown here:



.. code-block:: console

   $ renku workflow group --map input_file=step1.@input2 \
       -p input_file="The dataset to process"
       my-grouped-workflow step1 step2

You can also expose all inputs, outputs or parameters of child steps by
using ``--map-inputs``, ``--map-outputs`` or ``--map-params``, respectively.

On execution, renku will automatically detect links between steps, if an input
of one step uses the same path as an output of another step, and execute
them in the correct order. Since this depends on what values are passed
at runtime, you might want to enforce a certain order of steps by explicitely
mapping outputs to inputs.

You can do that using the ``--link <source>=<sink>`` parameters, e.g.
``--link step1.@output1=step2.@input1``. This gets recorded on the
workflow template and forces ``step2.@input1`` to always be set to the same
path as ``step1.@output1``, irrespective of which values are passed at
execution time.

This way, you can ensure that the steps in your workflow are always executed
in the correct order and that the dependencies between steps are modelled
correctly.

Renku can also add links for you automatically based on the default values
of inputs and outputs, where inputs/outputs that have the same path get
linked in the grouped run. To do this, pass the ``--link-all`` flag.

.. warning:: Due to workflows having to be directed acyclic graphs, cycles
   in the dependencies are not allowed. E.g. step1 depending on step2
   depending on step1 is not allowed. Additionally, the flow of information
   has to be from outputs to inputs or parameters, so you cannot map an input
   to an output, only the other way around.

Values on inputs/outputs/parameters get set according to the following
order of precedence (lower precedence first):

- Default value on a input/output/parameter
- Default value on a mapping to the input/output/parameter
- Value passed to a mapping to the input/output/parameter
- Value passed to the input/output/parameter
- Value propagated to an input from the source of a workflow link

"""


import click
from rich.console import Console
from rich.markdown import Markdown

from renku.cli.utils.callback import ClickCallback
from renku.core.commands.echo import ERROR
from renku.core.commands.view_model.composite_plan import CompositePlanViewModel
from renku.core.commands.view_model.plan import PlanViewModel
from renku.core.commands.workflow import (
    compose_workflow_command,
    create_workflow_command,
    list_workflows_command,
    remove_workflow_command,
    rename_workflow_command,
    set_workflow_name_command,
    show_workflow_command,
)


def _print_plan(plan: PlanViewModel):
    """Print a plan to stdout."""
    click.echo(click.style("Id: ", bold=True, fg="magenta") + click.style(plan.id, bold=True))
    click.echo(click.style("Name: ", bold=True, fg="magenta") + click.style(plan.name, bold=True))

    if plan.description:
        Console().print(Markdown(plan.description))

    click.echo(click.style("Command: ", bold=True, fg="magenta") + click.style(plan.full_command, bold=True))
    click.echo(click.style("Success Codes: ", bold=True, fg="magenta") + click.style(plan.success_codes, bold=True))

    if plan.inputs:
        click.echo(click.style("Inputs: ", bold=True, fg="magenta"))
        for run_input in plan.inputs:
            click.echo(click.style(f"\t- {run_input.name}:", bold=True))

            if run_input.description:
                click.echo(click.style(f"\t\t{run_input.description}"))

            click.echo(
                click.style("\t\tDefault Value: ", bold=True, fg="magenta")
                + click.style(run_input.default_value, bold=True)
            )

            if run_input.position:
                click.echo(
                    click.style("\t\tPosition: ", bold=True, fg="magenta") + click.style(run_input.position, bold=True)
                )

            if run_input.prefix:
                click.echo(
                    click.style("\t\tPrefix: ", bold=True, fg="magenta") + click.style(run_input.prefix, bold=True)
                )

    if plan.outputs:
        click.echo(click.style("Outputs: ", bold=True, fg="magenta"))
        for run_output in plan.outputs:
            click.echo(click.style(f"\t- {run_output.name}:", bold=True))

            if run_output.description:
                click.echo(click.style(f"\t\t{run_output.description}"))

            click.echo(
                click.style("\t\tDefault Value: ", bold=True, fg="magenta")
                + click.style(run_output.default_value, bold=True)
            )

            if run_output.position:
                click.echo(
                    click.style("\t\tPosition: ", bold=True, fg="magenta") + click.style(run_output.position, bold=True)
                )

            if run_output.prefix:
                click.echo(
                    click.style("\t\tPrefix: ", bold=True, fg="magenta") + click.style(run_output.prefix, bold=True)
                )

    if plan.parameters:
        click.echo(click.style("Parameters: ", bold=True, fg="magenta"))
        for run_parameter in plan.parameters:
            click.echo(click.style(f"\t- {run_parameter.name}:", bold=True))

            if run_parameter.description:
                click.echo(click.style(f"\t\t{run_parameter.description}"))

            click.echo(
                click.style("\t\tDefault Value: ", bold=True, fg="magenta")
                + click.style(run_parameter.default_value, bold=True)
            )

            if run_parameter.position:
                click.echo(
                    click.style("\t\tPosition: ", bold=True, fg="magenta")
                    + click.style(run_parameter.position, bold=True)
                )

            if run_parameter.prefix:
                click.echo(
                    click.style("\t\tPrefix: ", bold=True, fg="magenta") + click.style(run_parameter.prefix, bold=True)
                )


def _print_composite_plan(composite_plan: CompositePlanViewModel):
    """Print a CompositePlan to stdout."""
    click.echo(click.style("Id: ", bold=True, fg="magenta") + click.style(composite_plan.id, bold=True))
    click.echo(click.style("Name: ", bold=True, fg="magenta") + click.style(composite_plan.name, bold=True))

    if composite_plan.description:
        Console().print(Markdown(composite_plan.description))

    click.echo(click.style("Steps: ", bold=True, fg="magenta"))
    for step in composite_plan.steps:
        click.echo(click.style(f"\t- {step.name}:", bold=True))
        click.echo(click.style("\t\tId: ", bold=True, fg="magenta") + click.style(f"{step.id}", bold=True))

    if composite_plan.mappings:
        click.echo(click.style("Mappings: ", bold=True, fg="magenta"))
        for mapping in composite_plan.mappings:
            click.echo(click.style(f"\t- {mapping.name}:", bold=True))

            if mapping.description:
                click.echo(click.style(f"\t\t{mapping.description}"))

            click.echo(
                click.style("\t\tDefault Value: ", bold=True, fg="magenta")
                + click.style(mapping.default_value, bold=True)
            )
            click.echo(click.style("\tMaps to: ", bold=True, fg="magenta"))
            for maps_to in mapping.maps_to:
                click.style(maps_to, bold=True)

    if composite_plan.links:
        click.echo(click.style("Links: ", bold=True, fg="magenta"))
        for link in composite_plan.links:
            click.echo(click.style("\t- From: ", bold=True, fg="magenta") + click.style(link.source, bold=True))
            click.echo(click.style("\t\t To: ", bold=True, fg="magenta"))
            for sink in link.sinks:
                click.echo(click.style(f"\t\t- {sink}", bold=True))


@click.group()
def workflow():
    """Workflow commands."""
    pass


@workflow.command("ls")
def list_workflows():
    """List or manage workflows with subcommands."""
    communicator = ClickCallback()
    list_workflows_command().with_communicator(communicator).build().execute()


@workflow.command()
@click.argument("name_or_id", metavar="<name_or_id>")
def show(name_or_id):
    """Show details for workflow <name_or_id>."""
    plan = show_workflow_command().build().execute(name_or_id=name_or_id).output

    if plan:
        if isinstance(plan, PlanViewModel):
            _print_plan(plan)
        else:
            _print_composite_plan(plan)
    else:
        click.secho(ERROR + f"Workflow '{name_or_id}' not found.")


def validate_path(ctx, param, value):
    """Detect a workflow path if it is not passed."""
    # client = ctx.obj

    # if value is None:
    #     from renku.core.models.provenance.activity import ProcessRun

    #     activity = client.process_commit()

    #     if not isinstance(activity, ProcessRun):
    #         raise click.BadParameter("No tool was found.")

    #     return activity.path

    return value


@workflow.command("set-name")
@click.argument("name", metavar="<name>")
@click.argument(
    "path",
    metavar="<path>",
    type=click.Path(exists=True, dir_okay=False),
    callback=validate_path,
    default=None,
    required=False,
)
@click.option("--force", is_flag=True, help="Override the existence check.")
def set_name(name, path, force):
    """Sets the <name> for remote <path>."""
    set_workflow_name_command().build().execute(name=name, path=path, force=force)


@workflow.command()
@click.argument("old", metavar="<old>")
@click.argument("new", metavar="<new>")
@click.option("--force", is_flag=True, help="Override the existence check.")
def rename(old, new, force):
    """Rename the workflow named <old> to <new>."""
    rename_workflow_command().build().execute(old=old, new=new, force=force)


@workflow.command()
@click.argument("name", metavar="<name>")
def remove(name):
    """Remove the remote named <name>."""
    remove_workflow_command().build().execute(name=name)


@workflow.command()
@click.option("--revision", default="HEAD")
@click.option(
    "-o",
    "--output-file",
    metavar="FILE",
    type=click.Path(exists=False),
    default=None,
    help="Write workflow to the FILE.",
)
@click.argument("paths", type=click.Path(dir_okay=True), nargs=-1)
def create(output_file, revision, paths):
    """Create a workflow description for a file."""
    result = create_workflow_command().build().execute(output_file=output_file, revision=revision, paths=paths)

    if not output_file:
        click.echo(result.output)


@workflow.command()
@click.option("-d", "--description", help="Workflow step's description.")
@click.option("mappings", "-m", "--map", multiple=True, help="Mapping for a workflow parameter.")
@click.option("defaults", "-s", "--set", multiple=True, help="Default value for a workflow parameter.")
@click.option("links", "-l", "--link", multiple=True, help="Link source and sink parameters to connect steps.")
@click.option("-p", "--describe-param", multiple=True, help="Add description for a workflow parameter.")
@click.option("--map-inputs", is_flag=True, help="Exposes all child inputs as inputs on the CompositePlan.")
@click.option("--map-outputs", is_flag=True, help="Exposes all child outputs as outputs on the CompositePlan.")
@click.option("--map-params", is_flag=True, help="Exposes all child parameters as parameters on the CompositePlan.")
@click.option("--map-all", is_flag=True, help="Combination of --map-inputs, --map-outputs, --map-params.")
@click.option("--link-all", is_flag=True, help="Automatically link steps based on default values.")
@click.option("--keyword", multiple=True, help="List of keywords for the workflow.")
@click.argument("name", required=True)
@click.argument("steps", nargs=-1, required=True, type=click.UNPROCESSED)
def compose(
    description,
    mappings,
    defaults,
    links,
    describe_param,
    map_inputs,
    map_outputs,
    map_params,
    map_all,
    link_all,
    keyword,
    name,
    steps,
):
    """Create a composite workflow consisting of multiple steps."""

    if map_all:
        map_inputs = map_outputs = map_params = True

    result = (
        compose_workflow_command()
        .build()
        .execute(
            name=name,
            description=description,
            mappings=mappings,
            defaults=defaults,
            links=links,
            param_descriptions=describe_param,
            map_inputs=map_inputs,
            map_outputs=map_outputs,
            map_params=map_params,
            link_all=link_all,
            keywords=keyword,
            steps=steps,
        )
    )

    if not result.error:
        _print_composite_plan(result.output)
