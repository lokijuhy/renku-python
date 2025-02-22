..
    Copyright 2017-2021 - Swiss Data Science Center (SDSC)
    A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
    Eidgenössische Technische Hochschule Zürich (ETHZ).

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.


Repository API
==============

This API is built on top of Git and Git-LFS.

.. automodule:: renku.core.management
   :members:

Datasets
--------

.. automodule:: renku.core.management.datasets
   :members:

Repository
----------

.. automodule:: renku.core.management.repository
   :members:

Git Internals
-------------

.. automodule:: renku.core.management.git
   :members:

.. automodule:: renku.core.models.git
   :members:

Command Builder
---------------

Most renku commands require context (database/git/etc.) to be set up for them.
The command builder pattern makes this easy by wrapping commands in factory
methods.

.. automodule:: renku.core.management.command_builder
   :members:
