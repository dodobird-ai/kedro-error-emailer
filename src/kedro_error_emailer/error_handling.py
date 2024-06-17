from functools import wraps
import traceback
import socket
from datetime import datetime
from kedro.io import DataCatalog
from kedro.framework.context import KedroContext
import yaml
from .email import send_email_ses
import logging
from typing import Any
from .utils import select_arg_by_type, get_mailer_param, generate_error_info, get_email_credentials

logger = logging.getLogger(__name__)


def error_handler(hook_func):
    @wraps(hook_func)
    def wrapper(*args, **kwargs):
        try:
            if hook_func.__name__ in ["before_node_run", "on_node_error","after_node_run"]:
                raise TypeError(
                    f"Hook {hook_func.__name__} is not allowed to use @error_handler decorator. (It will be triggered by on_pipeline_error)"
                )
            return hook_func(*args, **kwargs)

        except Exception as e:
            print("Error in error_handler")
            hook_name = hook_func.__name__
            if hook_func.__name__ in ["before_node_run", "on_node_error","after_node_run"]:
                raise TypeError(
                    f"Hook {hook_func.__name__} is not allowed to use @error_handler decorator. (It will be triggered by on_pipeline_error)"
                )

            params = get_mailer_param(args)
            # Allow optional parameters, plus keeping it as None.
            ignored_exceptions = params.get("ignored_exceptions", []) or []
            if e.__class__.__name__ in ignored_exceptions:
                logger.warning(
                    f"Ignoring mailing for {e.__class__.__name__} error.")
                raise e
            
            ignored_envs = params.get("ignored_envs", []) or []
            if args[1].env in ignored_envs:
                logger.warning(f"Ignoring mailing for {e.__class__.__name__} environment.")

            hook_module = hook_func.__module__
            tb = traceback.TracebackException.from_exception(e)
            last_call = tb.stack[-1]
            filename = last_call.filename
            if hook_name == "on_pipeline_error":
                error_details = select_arg_by_type(args, dict)
                catalog = select_arg_by_type(args, DataCatalog)
                handle_error_on_pipeline_error(
                    e, error_details, catalog, hook_name, filename
                )
            elif hook_name == "after_pipeline_run":
                ending_params = select_arg_by_type(args, dict, on_conflict="first")
                catalog = select_arg_by_type(args, DataCatalog)
                handle_after_pipeline_run_error(
                    e, ending_params, catalog, hook_name, hook_module, filename
                )
            elif hook_name in ["after_catalog_created", "before_pipeline_run"]:
                catalog = select_arg_by_type(args, DataCatalog)
                handle_error_with_datacataglog(
                    e, catalog, hook_name, hook_module, filename
                )
            else:
                context = select_arg_by_type(args, KedroContext)
                handle_error_with_context(e, context, hook_name, hook_module)
            raise e

    return wrapper

def handle_error_with_datacataglog(
    e, catalog: DataCatalog, hook_name: str, location: str, filename: str
):
    mail_credentials = get_email_credentials()

    send_to = catalog.load("params:error_mailer.email.send_to")
    send_from = catalog.load("params:error_mailer.email.send_from")
    
    hostname = socket.gethostname()
    error_traceback = traceback.format_exc()
    project_name = location.split(".")[0]

    hook_info_extracted = {
        "Host Name": hostname,
        "Pipeline Name": project_name,
        "Hook Name": hook_name,
        "File": filename,
        "Error": str(e),
        "Traceback": error_traceback,
    }

    email_data = generate_error_info(catalog, hook_info_extracted)

    html_body = create_html_body(email_data)

    send_email_ses(
        send_from,
        send_to,
        f"Pipeline Error in {project_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        html_body,
        mail_credentials,
        html=True,
    )



def handle_after_pipeline_run_error(
    e, ending_params, catalog: DataCatalog, hook_name: str, location: str, filename: str
):
    mail_credentials = get_email_credentials()

    send_to = catalog.load("params:error_mailer.email.send_to")
    send_from = catalog.load("params:error_mailer.email.send_from")

    hostname = socket.gethostname()
    error_traceback = traceback.format_exc()
    runtime_params = ending_params["extra_params"]
    project_name = location.split(".")[0]
    env = ending_params["env"]

    hook_info_extracted = {
        "Host Name": hostname,
        "Pipeline Name": project_name,
        "Runtime Parameters": runtime_params,
        "Environment": env,
        "Hook Name": hook_name,
        "File": filename,
        "Error": str(e),
        "Traceback": error_traceback,
    }

    email_data = generate_error_info(catalog, hook_info_extracted)

    html_body = create_html_body(email_data)

    send_email_ses(
        send_from,
        send_to,
        f"Pipeline Error in {project_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        html_body,
        mail_credentials,
        html=True,
    )


def handle_error_on_pipeline_error(
    e, error_details: str, catalog: DataCatalog, hook_name: str, filename: str
):
    mail_credentials = get_email_credentials()

    catalog_extracted = catalog.load("parameters")

    send_to = catalog_extracted["error_mailer"]["email"]["send_to"]
    send_from = catalog_extracted["error_mailer"]["email"]["send_from"]

    env = error_details["env"]
    project_name = error_details["project_path"].split("/")[-1]

    runtime_params = error_details["extra_params"]
    error_traceback = traceback.format_exc()
    hostname = socket.gethostname()

    hook_info_extracted = {
        "Host Name": hostname,
        "Pipeline Name": project_name,
        "Runtime Parameters": runtime_params,
        "Environment": env,
        "File": filename,
        "Hook Name": hook_name,
        "Error": str(e),
        "Traceback": error_traceback,
    }

    email_data = generate_error_info(catalog, hook_info_extracted)

    html_body = create_html_body(email_data)

    send_email_ses(
        send_from,
        send_to,
        f"Pipeline Error in {project_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        html_body,
        mail_credentials,
        html=True,
    )


def handle_error_with_context(e, context: KedroContext, hook_name: str, location: str):
    send_to = context.params["error_mailer"]["email"]["send_to"]
    send_from = context.params["error_mailer"]["email"]["send_from"]

    mail_credentials = get_email_credentials()

    hostname = socket.gethostname()
    error_traceback = traceback.format_exc()
    runtime_params = context.config_loader.runtime_params
    project_name = str(context.project_path).split("/")[-1]

    hook_info_extracted = {
        "Host Name": hostname,
        "Pipeline Name": project_name,
        "Runtime Parameters": runtime_params,
        "Hook Name": location,
        "Function": hook_name,
        "Error": str(e),
        "Traceback": error_traceback,
    }

    mail_data = generate_error_info(context, hook_info_extracted)

    html_body = create_html_body(mail_data)

    send_email_ses(
        send_from,
        send_to,
        f"Pipeline Error in {project_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        html_body,
        mail_credentials,
        html=True,
    )


def create_html_body(error_info: dict):
    rows = "".join(
        f"<tr><th>{key}</th><td><pre>{value}</pre></td></tr>"
        for key, value in error_info.items()
    )

    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
                th {{ background-color: #f2f2f2; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; }}
            </style>
        </head>
        <body>
            <h2>Error Notification</h2>
            <p>An error has occurred in the pipeline execution.</p>
            <table>
                {rows}
            </table>
        </body>
    </html>
    """
    return html_content
