"""
This is an example of a Custom QueryExpectation.
For detailed information on QueryExpectations, please see:
    https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_query_expectations
"""

from typing import Any, Dict, Optional, Union

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.exceptions.exceptions import (
    InvalidExpectationConfigurationError,
)
from great_expectations.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation import (
    ExpectationValidationResult,
    QueryExpectation,
)


# <snippet>
class ExpectQueriedColumnValueFrequencyToMeetThreshold(QueryExpectation):
    # </snippet>
    # <snippet>
    """Expect the frequency of occurrences of a specified value in a queried column to be at least <threshold> percent of values in that column."""
    # </snippet>
    # <snippet>
    metric_dependencies = ("query.column",)
    # </snippet>
    # <snippet>
    query = """
            SELECT {col},
            CAST(COUNT({col}) AS float) / (SELECT COUNT({col}) FROM {active_batch})
            FROM {active_batch}
            GROUP BY {col}
            """
    # </snippet>
    # <snippet>
    success_keys = (
        "column",
        "value",
        "threshold",
        "query",
    )
    # </snippet>

    domain_keys = ("batch_id", "row_condition", "condition_parser")

    default_kwarg_values = {
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": False,
        "meta": None,
        "column": None,
        "value": None,
        "threshold": 1,
        "query": query,
    }

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration]
    ) -> None:
        super().validate_configuration(configuration)
        value = configuration["kwargs"].get("value")
        threshold = configuration["kwargs"].get("threshold")

        try:
            assert value is not None, "'value' must be specified"
            assert (isinstance(threshold, (int, float)) and 0 < threshold <= 1) or (
                isinstance(threshold, list)
                and all(isinstance(x, (int, float)) for x in threshold)
                and all([0 < x <= 1 for x in threshold])
                and 0 < sum(threshold) <= 1
            ), "'threshold' must be 1, a float between 0 and 1, or a list of floats whose sum is between 0 and 1"
            if isinstance(threshold, list):
                assert isinstance(value, list) and len(value) == len(
                    threshold
                ), "'value' and 'threshold' must contain the same number of arguments"
        except AssertionError as e:
            raise InvalidExpectationConfigurationError(str(e))

    # <snippet name="expect_queried_column_value_frequency_to_meet_threshold.py _validate function">
    # <snippet name="expect_queried_column_value_frequency_to_meet_threshold.py _validate function signature">
    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: dict,
        runtime_configuration: dict = None,
        execution_engine: ExecutionEngine = None,
    ) -> Union[ExpectationValidationResult, dict]:
        # </snippet>
        value = configuration["kwargs"].get("value")
        threshold = configuration["kwargs"].get("threshold")
        query_result = metrics.get("query.column")
        query_result = dict(query_result)

        if isinstance(value, list):
            success = all(
                query_result[value[i]] >= threshold[i] for i in range(len(value))
            )

            return {
                "success": success,
                "result": {
                    "observed_value": [
                        query_result[value[i]] for i in range(len(value))
                    ]
                },
            }

        success = query_result[value] >= threshold

        return {
            "success": success,
            "result": {"observed_value": query_result[value]},
        }
        # </snippet>

    # <snippet name="expect_queried_column_value_frequency_to_meet_threshold.py examples">
    examples = [
        {
            "data": [
                {
                    "dataset_name": "test",
                    "data": {
                        "col1": [1, 2, 2, 3, 4],
                        "col2": ["a", "a", "b", "b", "a"],
                    },
                },
            ],
            "tests": [
                {
                    "title": "basic_positive_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "column": "col2",
                        "value": "a",
                        "threshold": 0.6,
                    },
                    "out": {"success": True},
                    "only_for": ["sqlite", "spark"],
                },
                {
                    "title": "basic_negative_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "column": "col1",
                        "value": 2,
                        "threshold": 1,
                    },
                    "out": {"success": False},
                    "only_for": ["sqlite", "spark"],
                },
                {
                    "title": "multi_value_positive_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "column": "col2",
                        "value": ["a", "b"],
                        "threshold": [0.6, 0.4],
                    },
                    "out": {"success": True},
                    "only_for": ["sqlite", "spark"],
                },
                {
                    "title": "multi_value_positive_test_static_data_asset",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "column": "col2",
                        "value": ["a", "b"],
                        "threshold": [0.6, 0.4],
                        "query": """
                                 SELECT {col},
                                 CAST(COUNT({col}) AS float) / (SELECT COUNT({col}) FROM test)
                                 FROM test
                                 GROUP BY {col}
                                 """,
                    },
                    "out": {"success": True},
                    "only_for": ["sqlite"],
                },
                {
                    "title": "multi_value_positive_test_row_condition",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "column": "col2",
                        "value": ["a", "b"],
                        "threshold": [0.6, 0.4],
                        "row_condition": 'col("col1")==2',
                        "condition_parser": "great_expectations__experimental__",
                    },
                    "out": {"success": False},
                    "only_for": ["sqlite", "spark"],
                },
            ],
        },
    ]
    # </snippet>
    # <snippet name="expect_queried_column_value_frequency_to_meet_threshold.py library_metadata">
    # This dictionary contains metadata for display in the public gallery
    library_metadata = {
        "tags": ["query-based"],
        "contributors": ["@joegargery"],
    }
    # </snippet>


if __name__ == "__main__":
    # <snippet name="expect_queried_column_value_frequency_to_meet_threshold.py print_diagnostic_checklist()">
    ExpectQueriedColumnValueFrequencyToMeetThreshold().print_diagnostic_checklist()
    # </snippet>

# Note to users: code below this line is only for integration testing -- ignore!

diagnostics = ExpectQueriedColumnValueFrequencyToMeetThreshold().run_diagnostics()

for check in diagnostics["tests"]:
    assert check["test_passed"] is True
    assert check["error_diagnostics"] is None

for check in diagnostics["errors"]:
    assert check is None

for check in diagnostics["maturity_checklist"]["experimental"]:
    if check["message"] == "Passes all linting checks":
        continue
    assert check["passed"] is True
