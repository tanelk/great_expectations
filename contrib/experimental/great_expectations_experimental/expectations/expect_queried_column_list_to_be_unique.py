from typing import Optional, Union

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation import (
    ExpectationValidationResult,
    QueryExpectation,
)


class ExpectQueriedColumnListToBeUnique(QueryExpectation):
    """Expect multiple columns (such as a compound key) to be unique
    Args:
    *****
    template_dict: dict with the following keys:
        column_list - columns to check uniqueness on - separated by comma
    """

    metric_dependencies = ("query.template_values",)

    query = """
            SELECT COUNT(1) FROM (
            SELECT {column_list}, COUNT(1)
            FROM {active_batch}
            GROUP BY {column_list}
            HAVING count(1) > 1
            )
            """

    success_keys = ("template_dict" "query",)

    domain_keys = (
        "query",
        "template_dict",
        "batch_id",
    )
    default_kwarg_values = {
        "include_config": True,
        "catch_exceptions": False,
        "meta": None,
        "query": query,
    }

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration] = None
    ) -> None:
        """
        Validates that a configuration has been set, and sets a configuration if it has yet to be set. Ensures that
        necessary configuration arguments have been provided for the validation of the expectation.

        Args:
            configuration (OPTIONAL[ExpectationConfiguration]): \
                An optional Expectation Configuration entry that will be used to configure the expectation
        Returns:
            None. Raises InvalidExpectationConfigurationError if the config is not validated successfully
        """

        super().validate_configuration(configuration)
        if configuration is None:
            configuration = self.configuration

    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: dict,
        runtime_configuration: dict = None,
        execution_engine: ExecutionEngine = None,
    ) -> Union[ExpectationValidationResult, dict]:

        query_result = metrics.get("query.template_values")
        num_of_duplicates = query_result[0][0]

        if not num_of_duplicates:
            return {
                "info": "The columns are unique - no duplicates found",
                "success": True,
            }

        else:
            return {
                "success": False,
                "result": {
                    "info": f"{num_of_duplicates} Duplicated keys found",
                    "observed_value": num_of_duplicates,
                },
            }

    examples = [
        {
            "data": [
                {
                    "dataset_name": "test",
                    "data": {
                        "unique_num": [1, 2, 3, 4, 5, 6],
                        "unique_str": ["a", "b", "c", "d", "e", "f"],
                        "unique_str2": ["a", "b", "c", "d", "e", "f"],
                        "duplicate_num": [1, 1, 1, 1, 1, 1],
                        "duplicate_str": ["a", "a", "b", "c", "d", "e"],
                        "duplicate_str2": ["a", "a", "b", "c", "d", "e"],
                    },
                },
            ],
            "tests": [
                {
                    "title": "basic_positive_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "template_dict": {
                            "column_list": "unique_num,unique_str,unique_str2",
                        }
                    },
                    "out": {"success": True},
                    "only_for": ["sqlite"],
                },
                {
                    "title": "basic_negative_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "template_dict": {
                            "column_list": "duplicate_num,duplicate_str,duplicate_str2",
                        }
                    },
                    "out": {"success": False},
                    "only_for": ["sqlite"],
                },
            ],
        }
    ]

    library_metadata = {
        "tags": ["query-based"],
        "contributors": ["@itaise"],
    }


if __name__ == "__main__":
    ExpectQueriedColumnListToBeUnique().print_diagnostic_checklist()
