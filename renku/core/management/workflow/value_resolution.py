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
"""Resolution of ``Workflow`` execution values precedence."""

from abc import ABC, abstractmethod
from itertools import chain
from typing import Any, Dict, Set

from renku.core import errors
from renku.core.models.workflow.composite_plan import CompositePlan
from renku.core.models.workflow.parameter import ParameterMapping
from renku.core.models.workflow.plan import AbstractPlan, Plan


class ValueResolver(ABC):
    """Value resolution class for an ``AbstractPlan``."""

    def __init__(self, plan: AbstractPlan, values: Dict[str, Any]):
        self._values = values
        self.missing_parameters: Set[str] = set()
        self._plan = plan

    @abstractmethod
    def apply(self) -> AbstractPlan:
        """Applies values and default_values to a potentially nested workflow.

        :returns: The ``AbstractPlan`` with the user provided values set.
        """
        pass

    @staticmethod
    def get(plan: AbstractPlan, values: Dict[str, Any]) -> "ValueResolver":
        """Factory method to obtain the specific ValueResolver for a workflow.

        :param plan: a workflow.
        :param values: user defined dictionary of runtime values for the provided workflow.
        :returns: A ValueResolver object
        """
        return PlanValueResolver(plan, values) if isinstance(plan, Plan) else CompositePlanValueResolver(plan, values)


class PlanValueResolver(ValueResolver):
    """Value resolution class for a ``Plan``.

    Applies values and default_values to a workflow.
    """

    def __init__(self, plan: Plan, values: Dict[str, Any]):
        super(PlanValueResolver, self).__init__(plan, values)

    def apply(self) -> AbstractPlan:
        """Applies values and default_values to a ``Plan``."""
        if not self._values:
            return self._plan

        values_keys = set(self._values.keys())
        for param in chain(self._plan.inputs, self._plan.outputs, self._plan.parameters):
            if param.name in self._values:
                param.actual_value = self._values[param.name]
                values_keys.discard(param.name)

        self.missing_parameters = values_keys

        return self._plan


class CompositePlanValueResolver(ValueResolver):
    """Value resolution class for a ``CompositePlan``.

    Applies values and default_values to a nested workflow.

    Order of precedence is as follows (from lowest to highest):
    - Default value on a parameter
    - Default value on a mapping to the parameter
    - Value passed to a mapping to the parameter
    - Value passed to the parameter
    - Value propagated to a parameter from the source of a ParameterLink
    """

    def __init__(self, plan: CompositePlan, values: Dict[str, Any]):
        super(CompositePlanValueResolver, self).__init__(plan, values)

    def apply(self) -> AbstractPlan:
        """Applies values and default_values to a ``CompositePlan``."""

        if self._values:
            self._apply_parameters_values()

            for name, step in filter(lambda x: isinstance(x[1], dict), self._values.items()):
                child_workflow = next((w for w in self._plan.plans if w.name == name), None)
                if not child_workflow:
                    raise errors.ChildWorkflowNotFoundError(name, self._plan.name)

                rv = ValueResolver.get(child_workflow, step)
                _ = rv.apply()
                self.missing_parameters.update({f"{name}.{mp}" for mp in rv.missing_parameters})

        # apply defaults
        for mapping in self._plan.mappings:
            self._apply_parameter_defaults(mapping)

        apply_parameter_links(self._plan)

        return self._plan

    def _apply_parameter_defaults(self, mapping: ParameterMapping) -> None:
        """Apply default values to a mapping and contained params if they're not set already."""

        if not mapping.actual_value_set and mapping.default_value:
            mapping.actual_value = mapping.default_value

            for mapped_to in mapping.mapped_parameters:
                if isinstance(mapped_to, ParameterMapping):
                    self._apply_parameter_defaults(mapped_to)
                else:
                    if not mapped_to.actual_value_set:
                        mapped_to.actual_value = mapping.default_value

    def _apply_parameters_values(self) -> None:
        """Apply values to mappings of a CompositePlan."""
        for k, v in filter(lambda x: not isinstance(x[1], dict), self._values.items()):
            mapping = next((m for m in self._plan.mappings if m.name == k), None)

            if not mapping:
                self.missing_parameters.add(k)
                continue

            mapping.actual_value = v


def apply_parameter_links(workflow: CompositePlan) -> None:
    """Apply values from parameter links."""
    for link in workflow.links:
        for sink in link.sinks:
            sink.actual_value = link.source.actual_value

    for plan in workflow.plans:
        if isinstance(plan, CompositePlan):
            apply_parameter_links(plan)
