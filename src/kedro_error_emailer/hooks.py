from typing import Any
from kedro.pipeline import Pipeline
from kedro.io import DataCatalog
from kedro.framework.hooks import hook_impl
from .error_handling import error_handler, handle_error_on_pipeline_error


class MailerHook:
    @hook_impl
    def on_pipeline_error(
        self,
        error: Exception,
        run_params: dict[str, Any],
        pipeline: Pipeline,
        catalog: DataCatalog,
    ):
        handle_error_on_pipeline_error(
            error.args[0],
            run_params,
            catalog,
            "on_pipeline_error",
            "pipeline_verification_hooks",
        )
