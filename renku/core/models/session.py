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
"""Interactive session engine."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple


class ISessionProvider(metaclass=ABCMeta):
    """Abstract class for executing ``Plan``."""

    @abstractmethod
    def session_provider(self) -> Tuple["ISessionProvider", str]:
        """Supported session engine.

        :returns: a tuple of ``self`` and engine type name.
        """
        pass

    @abstractmethod
    def session_list(self, config: Path, client) -> List[str]:
        """Lists all the sessions currently running by the given session engine.

        :returns: a list of sessions.
        """
        pass

    @abstractmethod
    def session_start(self, config: Path, image_name: Optional[str], client) -> str:
        """Creates an interactive session.

        :returns: a unique id for the created interactive sesssion.
        """
        pass

    @abstractmethod
    def session_stop(self, client, session_name: Optional[str], stop_all: bool):
        """Stops all or a given interactive session."""
        pass

    @abstractmethod
    def session_url(self, session_name: str) -> str:
        """Get the given sessions URL."""
        pass
