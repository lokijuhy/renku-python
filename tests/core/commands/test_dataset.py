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
"""Dataset tests."""
import copy
import datetime
import os
import shutil
import stat
from pathlib import Path

import pytest

from renku.core import errors
from renku.core.commands.dataset import add_to_dataset, create_dataset, file_unlink, list_datasets, list_files
from renku.core.errors import ParameterError
from renku.core.management.datasets import DatasetsProvenance
from renku.core.management.repository import DEFAULT_DATA_DIR as DATA_DIR
from renku.core.metadata.repository import Repository
from renku.core.models.dataset import Dataset, is_dataset_name_valid
from renku.core.models.provenance.agent import Person
from renku.core.utils.contexts import chdir
from renku.core.utils.git import get_git_user
from renku.core.utils.urls import get_slug
from tests.utils import assert_dataset_is_mutated, load_dataset, raises


@pytest.mark.serial
@pytest.mark.parametrize(
    "scheme, path, overwrite, error",
    [
        ("", "temp", False, None),
        ("file://", "temp", True, None),
        ("", "tempp", False, errors.ParameterError),
        ("http://", "example.com/file1", False, None),
        ("https://", "example.com/file1", True, None),
        ("bla://", "file", False, errors.UrlSchemeNotSupported),
    ],
)
def test_data_add(scheme, path, overwrite, error, client_with_injection, directory_tree, dataset_responses):
    """Test data import."""
    with raises(error):
        if path == "temp":
            path = str(directory_tree / "file1")

        with client_with_injection.with_dataset(name="dataset", create=True, commit_database=True) as d:
            d.creators = [Person(name="me", email="me@example.com", id="me_id")]
            client_with_injection.add_data_to_dataset(d, ["{}{}".format(scheme, path)], overwrite=overwrite)

        target_path = os.path.join(DATA_DIR, "dataset", "file1")

        with open(target_path) as f:
            assert f.read() == "file1 content"

        assert d.find_file(target_path)

        # check that the imported file is read-only
        assert not os.access(target_path, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        # check the linking
        if scheme in ("", "file://"):
            shutil.rmtree("./data/dataset")
            with client_with_injection.with_dataset(name="dataset") as d:
                d.creators = [Person(name="me", email="me@example.com", id="me_id")]
                client_with_injection.add_data_to_dataset(d, ["{}{}".format(scheme, path)], overwrite=True)
            assert os.path.exists(target_path)


def test_data_add_recursive(directory_tree, client_with_injection):
    """Test recursive data imports."""
    with client_with_injection.with_dataset(name="dataset", create=True) as dataset:
        dataset.creators = [Person(name="me", email="me@example.com", id="me_id")]
        client_with_injection.add_data_to_dataset(dataset, [str(directory_tree / "dir1")])

        assert os.path.basename(os.path.dirname(dataset.files[0].entity.path)) == "dir1"


def test_creator_parse():
    """Test that different options for specifying creators work."""
    creator = Person(name="me", email="me@example.com")
    dataset = Dataset(name="dataset", creators=[creator])
    assert creator in dataset.creators

    # email check
    with pytest.raises(ValueError):
        Person(name="me", email="meexample.com")

    # creators must be a set or list of dicts or Person
    with pytest.raises(ValueError):
        Dataset(name="dataset", creators=["name"])


def test_creators_with_same_email(client_with_injection, load_dataset_with_injection):
    """Test creators with different names and same email address."""
    with client_with_injection.with_dataset(name="dataset", create=True, commit_database=True) as dataset:
        dataset.creators = [Person(name="me", email="me@example.com"), Person(name="me2", email="me@example.com")]
        DatasetsProvenance().add_or_update(dataset)

    dataset = load_dataset("dataset")

    assert 2 == len(dataset.creators)
    assert {c.name for c in dataset.creators} == {"me", "me2"}


def test_create_dataset_custom_message(project):
    """Test create dataset custom message."""
    create_dataset().with_commit_message("my dataset").with_database(write=True).build().execute(
        "ds1", title="", description="", creators=[]
    )

    last_commit = Repository(".").head.commit
    assert "my dataset" == last_commit.message.splitlines()[0]


def test_list_datasets_default(project):
    """Test a default dataset listing."""
    create_dataset().with_commit_message("my dataset").with_database(write=True).build().execute(
        "ds1", title="", description="", creators=[]
    )

    datasets = list_datasets().with_database().build().execute().output

    assert isinstance(datasets, list)
    assert "ds1" in [dataset.title for dataset in datasets]


def test_list_files_default(project, tmpdir):
    """Test a default file listing."""
    create_dataset().with_commit_message("my dataset").with_database(write=True).build().execute(
        "ds1", title="", description="", creators=[]
    )
    data_file = tmpdir / Path("some-file")
    data_file.write_text("1,2,3", encoding="utf-8")

    add_to_dataset().build().execute([str(data_file)], "ds1")
    files = list_files().build().execute(datasets=["ds1"]).output

    assert isinstance(files, list)
    assert "some-file" in [Path(f.entity.path).name for f in files]


def test_unlink_default(directory_tree, client):
    """Test unlink default behaviour."""
    with chdir(client.path):
        create_dataset().with_database(write=True).build().execute("dataset")
        add_to_dataset().with_database(write=True).build().execute([str(directory_tree / "dir1")], "dataset")

    with pytest.raises(ParameterError):
        file_unlink().build().execute("dataset", (), ())


@pytest.mark.xfail
def test_mutate(client):
    """Test metadata change after dataset mutation."""
    dataset = Dataset(
        name="my-dataset",
        creators=[Person.from_string("John Doe <john.doe@mail.com>")],
        date_published=datetime.datetime.now(datetime.timezone.utc),
        same_as="http://some-url",
    )
    old_dataset = copy.deepcopy(dataset)

    dataset.mutate()

    mutator = get_git_user(client.repository)
    assert_dataset_is_mutated(old=old_dataset, new=dataset, mutator=mutator)


@pytest.mark.xfail
def test_mutator_is_added_once(client):
    """Test mutator of a dataset is added only once to its creators list."""
    mutator = get_git_user(client.repository)

    dataset = Dataset(
        name="my-dataset",
        creators=[mutator],
        date_published=datetime.datetime.now(datetime.timezone.utc),
        same_as="http://some-url",
    )
    old_dataset = copy.deepcopy(dataset)

    dataset.mutate()

    assert_dataset_is_mutated(old=old_dataset, new=dataset, mutator=mutator)
    assert 1 == len(dataset.creators)


@pytest.mark.xfail
def test_mutate_is_done_once():
    """Test dataset mutation can be done only once."""
    dataset = Dataset(name="my-dataset", creators=[])
    before_id = dataset._id

    dataset.mutate()
    after_id = dataset._id

    assert before_id != after_id

    dataset.mutate()
    assert after_id == dataset._id


@pytest.mark.parametrize(
    "name, slug",
    [
        ("UPPER-CASE", "upper-case"),
        (" a name  ", "a_name"),
        ("..non-alphanumeric start or end-_", "non-alphanumeric_start_or_end"),
        ("double ..__._- non-alphanumeric", "double_non-alphanumeric"),
        ("double..dots", "double.dots"),
        ("nön-àsçîï", "non-ascii"),
        ("ends in .lock", "ends_in_lock"),
    ],
)
def test_dataset_name_slug(name, slug):
    """Test slug generation from name."""
    assert slug == get_slug(name)


def test_uppercase_dataset_name_is_valid():
    """Test dataset name can have uppercase characters."""
    assert is_dataset_name_valid("UPPER-CASE")
    assert is_dataset_name_valid("Pascal-Case")
