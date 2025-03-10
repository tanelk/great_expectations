from typing import TYPE_CHECKING, Dict, Optional

from great_expectations.core import (
    ExpectationConfiguration,
    ExpectationValidationResult,
)
from great_expectations.core.expectation_configuration import parse_result_format
from great_expectations.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation import (
    ColumnMapExpectation,
    _format_map_output,
    render_evaluation_parameter_string,
)
from great_expectations.render import (
    LegacyDiagnosticRendererType,
    LegacyRendererType,
    RenderedStringTemplateContent,
)
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    ParamSchemaType,
    RendererConfiguration,
)
from great_expectations.render.util import (
    num_to_str,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)
from great_expectations.validator.validator import ValidationDependencies

if TYPE_CHECKING:
    from great_expectations.render.renderer_configuration import RendererParams


class ExpectColumnValuesToBeNull(ColumnMapExpectation):
    """Expect the column values to be null.

    expect_column_values_to_be_null is a \
    [Column Map Expectation](https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_column_map_expectations).

    Args:
        column (str): \
            The column name.

    Keyword Args:
        mostly (None or a float between 0 and 1): \
            Successful if at least mostly fraction of values match the expectation. \
            For more detail, see [mostly](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#mostly).

    Other Parameters:
        result_format (str or None): \
            Which output mode to use: BOOLEAN_ONLY, BASIC, COMPLETE, or SUMMARY. \
        include_config (boolean): \
            If True, then include the expectation config as part of the result object.
        catch_exceptions (boolean or None): \
            If True, then catch exceptions and include them as part of the result object. \
            For more detail, see [catch_exceptions](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#catch_exceptions).
        meta (dict or None): \
            A JSON-serializable dictionary (nesting allowed) that will be included in the output without \
            modification. For more detail, see [meta](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#meta).

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

        Exact fields vary depending on the values passed to result_format, include_config, catch_exceptions, and meta.

    See Also:
        [expect_column_values_to_not_be_null](https://greatexpectations.io/expectations/expect_column_values_to_not_be_null)
    """

    # This dictionary contains metadata for display in the public gallery
    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column map expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }

    map_metric = "column_values.null"
    args_keys = ("column",)

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
        self.validate_metric_value_between_configuration(configuration=configuration)

    @classmethod
    def _prescriptive_template(
        cls, renderer_configuration: RendererConfiguration
    ) -> RendererConfiguration:
        add_param_args = (
            ("column", ParamSchemaType.STRING),
            ("mostly", ParamSchemaType.NUMBER),
            ("row_condition", ParamSchemaType.STRING),
            ("condition_parser", ParamSchemaType.STRING),
        )
        for name, schema_type in add_param_args:
            renderer_configuration.add_param(name=name, schema_type=schema_type)

        params: RendererParams = renderer_configuration.params

        if params.mostly and params.mostly.value < 1.0:
            renderer_configuration = cls._add_mostly_pct_param(
                renderer_configuration=renderer_configuration
            )
            template_str = "values must be null, at least $mostly_pct % of the time."
        else:
            template_str = "values must be null."

        if renderer_configuration.include_column_name:
            template_str = f"$column {template_str}"

        if params.row_condition:
            renderer_configuration = cls._add_row_condition_params(
                renderer_configuration=renderer_configuration
            )
            row_condition_str: str = cls._get_row_condition_string(
                renderer_configuration=renderer_configuration
            )
            template_str = f"{row_condition_str}, then {template_str}"

        renderer_configuration.template_str = template_str

        return renderer_configuration

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_evaluation_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        renderer_configuration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )
        params = substitute_none_for_missing(
            renderer_configuration.configuration.kwargs,
            ["column", "mostly", "row_condition", "condition_parser"],
        )

        if params["mostly"] is not None and params["mostly"] < 1.0:
            params["mostly_pct"] = num_to_str(
                params["mostly"] * 100, precision=15, no_scientific=True
            )
            # params["mostly_pct"] = "{:.14f}".format(params["mostly"]*100).rstrip("0").rstrip(".")
            template_str = "values must be null, at least $mostly_pct % of the time."
        else:
            template_str = "values must be null."

        if renderer_configuration.include_column_name:
            template_str = f"$column {template_str}"

        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(params["row_condition"])
            template_str = f"{conditional_template_str}, then {template_str}"
            params.update(conditional_params)

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": params,
                        "styling": renderer_configuration.styling,
                    },
                }
            )
        ]

    @classmethod
    @renderer(renderer_type=LegacyDiagnosticRendererType.OBSERVED_VALUE)
    def _diagnostic_observed_value_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ):
        result_dict = result.result

        try:
            notnull_percent = result_dict["unexpected_percent"]
            return (
                num_to_str(100 - notnull_percent, precision=5, use_locale=True)
                + "% null"
            )
        except KeyError:
            return "unknown % null"
        except TypeError:
            return "NaN% null"

    def get_validation_dependencies(
        self,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ) -> ValidationDependencies:
        validation_dependencies: ValidationDependencies = (
            super().get_validation_dependencies(
                configuration, execution_engine, runtime_configuration
            )
        )
        # We do not need this metric for a null metric
        validation_dependencies.remove_metric_configuration(
            metric_name="column_values.nonnull.unexpected_count"
        )
        return validation_dependencies

    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: Dict,
        runtime_configuration: Optional[dict] = None,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        result_format = self.get_result_format(
            configuration=configuration, runtime_configuration=runtime_configuration
        )
        mostly = self.get_success_kwargs().get(
            "mostly", self.default_kwarg_values.get("mostly")
        )
        total_count = metrics.get("table.row_count")
        unexpected_count = metrics.get(f"{self.map_metric}.unexpected_count")

        if total_count is None or total_count == 0:
            # Vacuously true
            success = True
        else:
            success_ratio = (total_count - unexpected_count) / total_count
            success = success_ratio >= mostly

        nonnull_count = None

        return _format_map_output(
            result_format=parse_result_format(result_format),
            success=success,
            element_count=metrics.get("table.row_count"),
            nonnull_count=nonnull_count,
            unexpected_count=metrics.get(f"{self.map_metric}.unexpected_count"),
            unexpected_list=metrics.get(f"{self.map_metric}.unexpected_values"),
            unexpected_index_list=metrics.get(
                f"{self.map_metric}.unexpected_index_list"
            ),
        )
