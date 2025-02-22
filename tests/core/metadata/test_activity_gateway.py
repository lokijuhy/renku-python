# -*- coding: utf-8 -*-
#
# Copyright 2017-2021- Swiss Data Science Center (SDSC)
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
"""Test activity database gateways."""


from renku.core.metadata.gateway.activity_gateway import ActivityGateway
from renku.core.models.workflow.plan import Plan
from tests.utils import create_dummy_activity


def test_activity_gateway_downstream_activities(dummy_database_injection_manager):
    """test getting downstream activities work."""
    plan = Plan(id=Plan.generate_id(), name="plan")

    intermediate = create_dummy_activity(plan=plan, usages=["some/data"], generations=["other/data/file"])
    previous = create_dummy_activity(plan=plan, generations=["some/"])
    following = create_dummy_activity(plan=plan, usages=["other/data"])
    unrelated = create_dummy_activity(plan=plan, usages=["unrelated_in"], generations=["unrelated_out"])

    with dummy_database_injection_manager(None):
        activity_gateway = ActivityGateway()

        activity_gateway.add(intermediate)
        activity_gateway.add(following)
        activity_gateway.add(previous)
        activity_gateway.add(unrelated)

        downstream = activity_gateway.get_downstream_activities(following)

        assert not downstream

        downstream = activity_gateway.get_downstream_activities(intermediate)
        assert {following.id} == {a.id for a in downstream}

        downstream = activity_gateway.get_downstream_activities(previous)
        assert {following.id, intermediate.id} == {a.id for a in downstream}


def test_activity_gateway_downstream_activity_chains(dummy_database_injection_manager):
    """test getting downstream activity chains work."""
    r1 = create_dummy_activity(plan="r1", usages=["a"], generations=["b"])
    r2 = create_dummy_activity(plan="r2", usages=["b"], generations=["c"])
    r3 = create_dummy_activity(plan="r3", usages=["d"], generations=["e"])
    r4 = create_dummy_activity(plan="r4", usages=["c", "e"], generations=["f", "g"])
    r5 = create_dummy_activity(plan="r5", usages=["f"], generations=["h"])
    r6 = create_dummy_activity(plan="r6", usages=["g"], generations=["i"])
    r7 = create_dummy_activity(plan="r7", usages=["x"], generations=["y"])

    with dummy_database_injection_manager(None):
        activity_gateway = ActivityGateway()

        activity_gateway.add(r1)
        activity_gateway.add(r3)
        activity_gateway.add(r2)
        activity_gateway.add(r4)
        activity_gateway.add(r5)
        activity_gateway.add(r6)
        activity_gateway.add(r7)

        assert [] == activity_gateway.get_downstream_activity_chains(r6)

        downstream_chains = activity_gateway.get_downstream_activity_chains(r1)
        assert {(r2.id,), (r2.id, r4.id), (r2.id, r4.id, r5.id), (r2.id, r4.id, r6.id)} == {
            tuple(a.id for a in chain) for chain in downstream_chains
        }

        downstream_chains = activity_gateway.get_downstream_activity_chains(r4)
        assert {(r5.id,), (r6.id,)} == {tuple(a.id for a in chain) for chain in downstream_chains}

        assert [] == activity_gateway.get_downstream_activity_chains(r7)


def test_activity_gateway_upstream_activity_chains(dummy_database_injection_manager):
    """test getting upstream activity chains work."""
    r1 = create_dummy_activity(plan="r1", usages=["a"], generations=["b"])
    r2 = create_dummy_activity(plan="r2", usages=["b"], generations=["c"])
    r3 = create_dummy_activity(plan="r3", usages=["d"], generations=["e"])
    r4 = create_dummy_activity(plan="r4", usages=["c", "e"], generations=["f", "g"])
    r5 = create_dummy_activity(plan="r5", usages=["f"], generations=["h"])
    r6 = create_dummy_activity(plan="r6", usages=["g"], generations=["i"])
    r7 = create_dummy_activity(plan="r7", usages=["x"], generations=["y"])

    with dummy_database_injection_manager(None):
        activity_gateway = ActivityGateway()

        activity_gateway.add(r1)
        activity_gateway.add(r3)
        activity_gateway.add(r2)
        activity_gateway.add(r4)
        activity_gateway.add(r5)
        activity_gateway.add(r6)
        activity_gateway.add(r7)

        assert [] == activity_gateway.get_upstream_activity_chains(r1)

        downstream_chains = activity_gateway.get_upstream_activity_chains(r6)
        assert {(r4.id,), (r4.id, r3.id), (r4.id, r2.id), (r4.id, r2.id, r1.id)} == {
            tuple(a.id for a in chain) for chain in downstream_chains
        }

        downstream_chains = activity_gateway.get_upstream_activity_chains(r4)
        assert {(r3.id,), (r2.id,), (r2.id, r1.id)} == {tuple(a.id for a in chain) for chain in downstream_chains}

        assert [] == activity_gateway.get_upstream_activity_chains(r7)
