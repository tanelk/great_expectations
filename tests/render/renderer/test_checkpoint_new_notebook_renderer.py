import os
import shutil

import nbformat
import pytest

import great_expectations as gx
from great_expectations import DataContext
from great_expectations.data_context import BaseDataContext
from great_expectations.data_context.util import file_relative_path
from great_expectations.render.renderer.checkpoint_new_notebook_renderer import (
    CheckpointNewNotebookRenderer,
)


@pytest.fixture
def assetless_dataconnector_context(
    tmp_path_factory,
    monkeypatch,
):
    # Re-enable GE_USAGE_STATS
    monkeypatch.delenv("GE_USAGE_STATS")

    project_path = str(tmp_path_factory.mktemp("titanic_data_context"))
    context_path = os.path.join(project_path, "great_expectations")
    os.makedirs(os.path.join(context_path, "expectations"), exist_ok=True)
    data_path = os.path.join(context_path, "..", "data", "titanic")
    os.makedirs(os.path.join(data_path), exist_ok=True)
    shutil.copy(
        file_relative_path(
            __file__,
            "../../test_fixtures/great_expectations_v013_no_datasource_stats_enabled.yml",
        ),
        str(os.path.join(context_path, "great_expectations.yml")),
    )
    context = gx.data_context.DataContext(context_path)
    assert context.root_directory == context_path

    datasource_config = f"""
            class_name: Datasource

            execution_engine:
                class_name: PandasExecutionEngine

            data_connectors:
                my_other_data_connector:
                    class_name: ConfiguredAssetFilesystemDataConnector
                    base_directory: {data_path}
                    glob_directive: "*.csv"

                    default_regex:
                        pattern: (.+)\\.csv
                        group_names:
                            - name
                    assets:
                        {{}}
            """

    context.test_yaml_config(
        name="my_datasource", yaml_config=datasource_config, pretty_print=False
    )
    # noinspection PyProtectedMember
    context._save_project_config()
    return context


def test_find_datasource_with_asset_on_context_with_no_datasources(
    empty_data_context,
):
    context = empty_data_context
    assert len(context.list_datasources()) == 0

    renderer = CheckpointNewNotebookRenderer(context, "foo")
    obs = renderer._find_datasource_with_asset()
    assert obs is None


def test_find_datasource_with_asset_on_context_with_a_datasource_with_no_dataconnectors(
    titanic_pandas_data_context_with_v013_datasource_stats_enabled_with_checkpoints_v1_with_templates,
):
    context = titanic_pandas_data_context_with_v013_datasource_stats_enabled_with_checkpoints_v1_with_templates
    context.delete_datasource("my_datasource")
    assert len(context.list_datasources()) == 0
    context.add_datasource(
        "aaa_datasource",
        class_name="Datasource",
        module_name="great_expectations.datasource.new_datasource",
        execution_engine={
            "class_name": "PandasExecutionEngine",
            "module_name": "great_expectations.execution_engine",
        },
    )
    assert len(context.list_datasources()) == 1

    renderer = CheckpointNewNotebookRenderer(context, "foo")
    obs = renderer._find_datasource_with_asset()
    assert obs is None


@pytest.mark.slow  # 2.27s
def test_find_datasource_with_asset_on_context_with_a_datasource_with_a_dataconnector_that_has_no_assets(
    assetless_dataconnector_context,
):
    context = assetless_dataconnector_context
    assert list(context.get_datasource("my_datasource").data_connectors.keys()) == [
        "my_other_data_connector"
    ]

    # remove data asset name
    config = context.get_config_with_variables_substituted()
    root_directory = context.root_directory

    context = BaseDataContext(project_config=config, context_root_dir=root_directory)

    renderer = CheckpointNewNotebookRenderer(context, "foo")
    obs = renderer._find_datasource_with_asset()
    assert obs is None


def test_find_datasource_with_asset_on_happy_path_context(
    deterministic_asset_dataconnector_context,
):
    context = deterministic_asset_dataconnector_context
    assert len(context.list_datasources()) == 1

    renderer = CheckpointNewNotebookRenderer(context, "foo")
    obs = renderer._find_datasource_with_asset()

    assert obs == {
        "asset_name": "users",
        "data_connector_name": "my_other_data_connector",
        "datasource_name": "my_datasource",
    }


def test_find_datasource_with_asset_on_context_with_a_full_datasource_and_one_with_no_dataconnectors(
    deterministic_asset_dataconnector_context,
):
    context = deterministic_asset_dataconnector_context
    assert len(context.list_datasources()) == 1
    context.add_datasource(
        "aaa_datasource",
        class_name="Datasource",
        module_name="great_expectations.datasource.new_datasource",
        execution_engine={
            "class_name": "PandasExecutionEngine",
            "module_name": "great_expectations.execution_engine",
        },
    )
    assert len(context.list_datasources()) == 2

    renderer = CheckpointNewNotebookRenderer(context, "foo")
    obs = renderer._find_datasource_with_asset()
    assert obs == {
        "datasource_name": "my_datasource",
        "data_connector_name": "my_other_data_connector",
        "asset_name": "users",
    }


@pytest.fixture
def checkpoint_new_notebook_assets():
    header = [
        {
            "cell_type": "markdown",
            "source": "# Create Your Checkpoint\nUse this notebook to configure a new Checkpoint and add it to your project:\n\n**Checkpoint Name**: `my_checkpoint_name`",
            "metadata": {},
        }
    ]
    imports = [
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "source": "from ruamel.yaml import YAML\nimport great_expectations as gx\nfrom pprint import pprint\n\nyaml = YAML()\ncontext = gx.get_context()",
            "outputs": [],
        },
    ]
    optional_customize_your_config = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": """# Customize Your Configuration\nThe following cells show examples for listing your current configuration. You can replace values in the sample configuration with these values to customize your Checkpoint.""",
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "source": """# Run this cell to print out the names of your Datasources, Data Connectors and Data Assets\npprint(context.get_available_data_asset_names())""",
            "outputs": [],
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "source": "context.list_expectation_suite_names()",
            "outputs": [],
        },
    ]

    sample_checkpoint_config_markdown_description = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": """# Create a Checkpoint Configuration\n\n**If you are new to Great Expectations or the Checkpoint feature**, you should start with SimpleCheckpoint because it includes default configurations like a default list of post validation actions.\n\nIn the cell below we have created a sample Checkpoint configuration using **your configuration** and **SimpleCheckpoint** to run a single validation of a single Expectation Suite against a single Batch of data.\n\nTo keep it simple, we are just choosing the first available instance of each of the following items you have configured in your Data Context:\n* Datasource\n* DataConnector\n* DataAsset\n* Partition\n* Expectation Suite\n\nOf course this is purely an example, you may edit this to your heart's content.\n\n**My configuration is not so simple - are there more advanced options?**\n\nGlad you asked! Checkpoints are very versatile. For example, you can validate many Batches in a single Checkpoint, validate Batches against different Expectation Suites or against many Expectation Suites, control the specific post-validation actions based on Expectation Suite / Batch / results of validation among other features. Check out our documentation on Checkpoints for more details and for instructions on how to implement other more advanced features including using the **Checkpoint** class:\n- https://docs.greatexpectations.io/docs/reference/checkpoints_and_actions\n- https://docs.greatexpectations.io/docs/guides/validation/checkpoints/how_to_create_a_new_checkpoint\n- https://docs.greatexpectations.io/docs/guides/validation/checkpoints/how_to_configure_a_new_checkpoint_using_test_yaml_config""",
        },
    ]
    sample_checkpoint_config_code_correct = [
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "source": (
                'my_checkpoint_name = "my_checkpoint_name"  # This was populated from your CLI command.\n\n'
                'yaml_config = f"""\n'
                "name: {my_checkpoint_name}\n"
                """config_version: 1.0
class_name: SimpleCheckpoint
run_name_template: "%Y%m%d-%H%M%S-my-run-name-template"
validations:
  - batch_request:
      datasource_name: my_datasource
      data_connector_name: my_other_data_connector
      data_asset_name: users
      data_connector_query:
        index: -1
    expectation_suite_name: Titanic.warning
"""
                '"""'
                "\nprint(yaml_config)"
            ),
            "outputs": [],
        },
    ]
    sample_checkpoint_config_markdown_error_message = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "Sorry, we were unable to create a sample configuration. Perhaps you don't have a Datasource or Expectation Suite configured.",
        },
    ]

    test_and_save_your_checkpoint_configuration = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": """# Test Your Checkpoint Configuration\nHere we will test your Checkpoint configuration to make sure it is valid.\n\nThis `test_yaml_config()` function is meant to enable fast dev loops. If your configuration is correct, this cell will show a message that you successfully instantiated a Checkpoint. You can continually edit your Checkpoint config yaml and re-run the cell to check until the new config is valid.\n\nIf you instead wish to use python instead of yaml to configure your Checkpoint, you can use `context.add_checkpoint()` and specify all the required parameters.""",
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "source": """my_checkpoint = context.test_yaml_config(yaml_config=yaml_config)""",
            "outputs": [],
        },
    ]
    review_checkpoint = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": """# Review Your Checkpoint\n\nYou can run the following cell to print out the full yaml configuration. For example, if you used **SimpleCheckpoint**  this will show you the default action list.""",
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "source": 'print(my_checkpoint.get_config(mode="yaml"))',
            "outputs": [],
        },
    ]
    add_checkpoint = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": """# Add Your Checkpoint\n\nRun the following cell to save this Checkpoint to your Checkpoint Store.""",
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "source": "context.add_checkpoint(**yaml.load(yaml_config))",
            "outputs": [],
        },
    ]
    optional_run_checkpoint = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": """# Run Your Checkpoint & Open Data Docs(Optional)\n\nYou may wish to run the Checkpoint now and review its output in Data Docs. If so uncomment and run the following cell.""",
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "source": "# context.run_checkpoint(checkpoint_name=my_checkpoint_name)\n# context.open_data_docs()",
            "outputs": [],
        },
    ]

    return {
        "header": header,
        "imports": imports,
        "optional_customize_your_config": optional_customize_your_config,
        "sample_checkpoint_config_markdown_description": sample_checkpoint_config_markdown_description,
        "sample_checkpoint_config_code_correct": sample_checkpoint_config_code_correct,
        "sample_checkpoint_config_markdown_error_message": sample_checkpoint_config_markdown_error_message,
        "test_and_save_your_checkpoint_configuration": test_and_save_your_checkpoint_configuration,
        "review_checkpoint": review_checkpoint,
        "add_checkpoint": add_checkpoint,
        "optional_run_checkpoint": optional_run_checkpoint,
    }


@pytest.mark.slow  # 1.10s
def test_render_checkpoint_new_notebook_with_available_data_asset(
    deterministic_asset_dataconnector_context,
    titanic_expectation_suite,
    checkpoint_new_notebook_assets,
):
    """
    What does this test and why?
    The CheckpointNewNotebookRenderer should generate a notebook with an example SimpleCheckpoint yaml config based on the first available data asset.
    """

    context: DataContext = deterministic_asset_dataconnector_context

    assert context.list_checkpoints() == []
    context.save_expectation_suite(titanic_expectation_suite)
    assert context.list_expectation_suite_names() == ["Titanic.warning"]

    checkpoint_new_notebook_renderer = CheckpointNewNotebookRenderer(
        context=context, checkpoint_name="my_checkpoint_name"
    )
    obs: nbformat.NotebookNode = checkpoint_new_notebook_renderer.render()

    assert isinstance(obs, dict)

    expected_cells = (
        checkpoint_new_notebook_assets["header"]
        + checkpoint_new_notebook_assets["imports"]
        + checkpoint_new_notebook_assets[
            "sample_checkpoint_config_markdown_description"
        ]
        # Testing to make sure everything in the notebook but especially this checkpoint config code is correct.
        + checkpoint_new_notebook_assets["sample_checkpoint_config_code_correct"]
        + checkpoint_new_notebook_assets["optional_customize_your_config"]
        + checkpoint_new_notebook_assets["test_and_save_your_checkpoint_configuration"]
        + checkpoint_new_notebook_assets["review_checkpoint"]
        + checkpoint_new_notebook_assets["add_checkpoint"]
        + checkpoint_new_notebook_assets["optional_run_checkpoint"]
    )

    expected = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {},
        "cells": expected_cells,
    }

    del expected["nbformat_minor"]
    del obs["nbformat_minor"]
    for obs_cell, expected_cell in zip(obs["cells"], expected["cells"]):
        obs_cell.pop("id", None)
        assert obs_cell == expected_cell
    assert obs == expected


def test_render_checkpoint_new_notebook_with_unavailable_data_asset(
    assetless_dataconnector_context,
    checkpoint_new_notebook_assets,
):
    context: DataContext = assetless_dataconnector_context

    assert context.list_checkpoints() == []

    # This config is bad because of a missing expectation suite

    checkpoint_new_notebook_renderer = CheckpointNewNotebookRenderer(
        context=context, checkpoint_name="my_checkpoint_name"
    )
    obs: nbformat.NotebookNode = checkpoint_new_notebook_renderer.render()

    assert isinstance(obs, dict)

    expected_cells = (
        checkpoint_new_notebook_assets["header"]
        + checkpoint_new_notebook_assets["imports"]
        + checkpoint_new_notebook_assets[
            "sample_checkpoint_config_markdown_description"
        ]
        # Testing to make sure the error message here is displayed appropriately
        + checkpoint_new_notebook_assets[
            "sample_checkpoint_config_markdown_error_message"
        ]
        + checkpoint_new_notebook_assets["optional_customize_your_config"]
        + checkpoint_new_notebook_assets["test_and_save_your_checkpoint_configuration"]
        + checkpoint_new_notebook_assets["review_checkpoint"]
        + checkpoint_new_notebook_assets["add_checkpoint"]
        + checkpoint_new_notebook_assets["optional_run_checkpoint"]
    )

    expected = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {},
        "cells": expected_cells,
    }

    del expected["nbformat_minor"]
    del obs["nbformat_minor"]
    for obs_cell, expected_cell in zip(obs["cells"], expected["cells"]):
        obs_cell.pop("id", None)
        assert obs_cell == expected_cell
    assert obs == expected
