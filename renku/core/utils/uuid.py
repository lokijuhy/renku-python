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
"""Helper utils for handling UUIDs."""
import uuid


def is_uuid(value):
    """Check if value is UUID4.

    Copied from https://stackoverflow.com/questions/19989481/
    """
    try:
        uuid_obj = uuid.UUID(value, version=4)
    except ValueError:
        return False

    return str(uuid_obj) == value
