# -*- coding: utf-8 -*-
#
# Copyright 2017-2022 - Swiss Data Science Center (SDSC)
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
"""Template variable utility methods."""

import datetime
from jinja2 import Environment

from typing import Dict, Iterable

from renku.core import errors


def date_cast(date):
    """Casts any object into a datetime.datetime object date"""
    if date is None:
        return datetime.datetime.now()
    elif isinstance(date, datetime.datetime):
        return date

    # fuzzy date
    try:
        if isinstance(date, str):
            # not parsed yet, obviously a timestamp?
            if date.isdigit():
                date = int(date)
            else:
                date = float(date)

        return datetime.datetime.fromtimestamp(date)
    except Exception:
        raise errors.ParameterError(f"Unable to parse {date} as datetime.")


def strftime(date=None, format="%Y-%m-%d") -> str:
    return date_cast(date).strftime(format)


class TemplateVar:
    def __init__(self):
        self.jinja2_env = Environment(variable_start_string="{", variable_end_string="}")
        self.jinja2_env.filters["strftime"] = strftime

    def apply(self, param: str, parameters: Dict[str, str]) -> str:
        breakpoint()
        return self.jinja2_env.from_string(param).render(parameters)

    @staticmethod
    def to_map(parameters: Iterable[str]) -> Dict[str, str]:
        return dict(map(lambda x: (x.name, x.actual_value), parameters))
