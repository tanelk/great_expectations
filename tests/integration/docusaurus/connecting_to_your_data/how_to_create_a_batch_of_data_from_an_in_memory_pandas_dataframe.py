# <snippet>
import pandas as pd
from ruamel import yaml

import great_expectations as gx
from great_expectations import DataContext
from great_expectations.core import ExpectationSuite
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.validator.validator import Validator

# </snippet>

# <snippet>
context: DataContext = gx.get_context()
# </snippet>

# create and load Expectation Suite
# <snippet>
context.create_expectation_suite(
    expectation_suite_name="insert_your_expectation_suite_name_here"
)
# </snippet>
# <snippet>
suite: ExpectationSuite = context.get_expectation_suite(
    expectation_suite_name="insert_your_expectation_suite_name_here"
)
# </snippet>

# <snippet>
datasource_yaml = f"""
name: my_pandas_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
    my_runtime_data_connector:
        class_name: RuntimeDataConnector
        batch_identifiers:
            - some_key_maybe_pipeline_stage
            - some_other_key_maybe_airflow_run_id
"""
# </snippet>

# <snippet>
context.add_datasource(**yaml.load(datasource_yaml))
# </snippet>

# RuntimeBatchRequest with batch_data as Pandas Dataframe
# <snippet>
path_to_file: str = "some_path.csv"
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
path_to_file: str = "./data/yellow_tripdata_sample_2019-01.csv"

# <snippet>
df: pd.DataFrame = pd.read_csv(path_to_file)
# </snippet>
# <snippet>
runtime_batch_request = RuntimeBatchRequest(
    datasource_name="my_pandas_datasource",
    data_connector_name="my_runtime_data_connector",
    data_asset_name="insert_your_data_asset_name_here",
    runtime_parameters={"batch_data": df},
    batch_identifiers={
        "some_key_maybe_pipeline_stage": "ingestion step 1",
        "some_other_key_maybe_airflow_run_id": "run 18",
    },
)
# </snippet>

# RuntimeBatchRequest with path
# <snippet>
runtime_batch_request = RuntimeBatchRequest(
    datasource_name="my_pandas_datasource",
    data_connector_name="my_runtime_data_connector",
    data_asset_name="insert_your_data_asset_name_here",
    runtime_parameters={"path": path_to_file},
    batch_identifiers={
        "some_key_maybe_pipeline_stage": "ingestion step 1",
        "some_other_key_maybe_airflow_run_id": "run 18",
    },
    batch_spec_passthrough={
        "reader_method": "read_csv",
        "reader_options": {"sep": ",", "header": 0},
    },
)
# </snippet>

# Constructing Validator by passing in RuntimeBatchRequest
# <snippet>
my_validator: Validator = context.get_validator(
    batch_request=runtime_batch_request,
    expectation_suite=suite,  # OR
    # expectation_suite_name=suite_name
)
# </snippet>
# my_validator.head()

# Constructing Validator by passing in arguments
# <snippet>
my_validator: Validator = context.get_validator(
    datasource_name="my_pandas_datasource",
    data_connector_name="my_runtime_data_connector",
    data_asset_name="insert_your_data_asset_name_here",
    runtime_parameters={"path": path_to_file},
    batch_identifiers={
        "some_key_maybe_pipeline_stage": "ingestion step 1",
        "some_other_key_maybe_airflow_run_id": "run 18",
    },
    batch_spec_passthrough={
        "reader_method": "read_csv",
        "reader_options": {"sep": ",", "header": 0},
    },
    expectation_suite=suite,  # OR
    # expectation_suite_name=suite_name
)
# </snippet>
# <snippet>
my_validator.head()
# </snippet>
