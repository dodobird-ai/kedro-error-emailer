from typing import Any
from kedro.pipeline import Pipeline
from kedro.io import DataCatalog
from kedro.framework.hooks import hook_impl
from .error_handling import handle_error_on_pipeline_error
import logging

logger = logging.getLogger(__name__)


class MailerHook:
    @hook_impl
    def on_pipeline_error(
        self,
        error: Exception,
        run_params: dict[str, Any],
        pipeline: Pipeline,
        catalog: DataCatalog,
    ):
        # Create a variable to store the error message
        error_message = error.args[0]

        # Add a verification step before handling the error
        if not error_message:
            logger.error("No error message found.")
            
        handle_error_on_pipeline_error(
            error_message,
            run_params,
            catalog,
            "on_pipeline_error",
            "pipeline_verification_hooks",
        )

