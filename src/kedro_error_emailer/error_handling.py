from functools import wraps
import traceback
import socket
from datetime import datetime
from kedro.io import DataCatalog
from kedro.framework.context import KedroContext
import yaml
from .email import send_email_ses

#TODO: Add error type to ignore from the mailing in the catalog
def error_handler(hook_func):
    @wraps(hook_func)
    def wrapper(*args, **kwargs):
        try:
            return hook_func(*args, **kwargs)
        except Exception as e:
            hook_name = hook_func.__name__
            hook_module = hook_func.__module__

            tb = traceback.TracebackException.from_exception(e)
            last_call = tb.stack[-1]
            filename = last_call.filename
            #TODO: Raise error if the hook use where should not be used
            #TODO: change args getter with index to by type needed
            if hook_name == "on_pipeline_error":
                handle_error_on_pipeline_error(e, args[2], args[4], hook_name, filename)
            if hook_name == "after_pipeline_run":
                handle_after_pipeline_run_error(e, args[1], args[4], hook_name, hook_module, filename)
            else:
                handle_error_with_context(e, args[1], hook_name, hook_module)  
            raise e
    return wrapper

def handle_after_pipeline_run_error(e, ending_params, catalog: DataCatalog, hook_name: str, location: str, filename: str):
    local_path = catalog.load("params:local_conf_path") + "credentials.yml"
    with open(local_path, "r") as f:
        credentials = yaml.safe_load(f)
    
    send_to = catalog.load("params:mailer.send_to")
    send_from = catalog.load("params:mailer.send_from")  
    mail_credentials = credentials["email_access"]

    hostname = socket.gethostname()
    error_traceback = traceback.format_exc()
    tenant_id = catalog.load("params:tenant_id")
    runtime_params = ending_params["extra_params"]
    env = ending_params["env"]
    project_name = location.split(".")[0]

    error_info = {
        "Tenant ID": tenant_id,
        "Host Name": hostname,
        "Pipeline Name": project_name,
        "Runtime Parameters": runtime_params,
        "Environment": env,
        "Location": hook_name,
        "File": filename,
        "Error": str(e),
        "Traceback": error_traceback
    }

    html_body = create_html_body(error_info)
    send_email_ses(send_from, send_to, f"Pipeline Error in {project_name} - {tenant_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", html_body, mail_credentials, html=True)

def handle_error_on_pipeline_error(e, error_details: str, catalog: DataCatalog, hook_name: str, filename: str):
    local_path = error_details["extra_params"]["local_conf_path"] + "credentials.yml"
    with open(local_path, "r") as f:
        credentials = yaml.safe_load(f)

    catalog_extracted = catalog.load("parameters")

    send_to = catalog_extracted["mailer"]["send_to"]
    send_from = catalog_extracted["mailer"]["send_from"]  
    mail_credentials = credentials["email_access"]

    hostname = socket.gethostname()
    error_traceback = traceback.format_exc()
    tenant_id = catalog_extracted["tenant_id"]
    runtime_params = error_details["extra_params"]
    env = error_details["env"]
    project_name = error_details["project_path"].split("/")[-1]

    error_info = {
        "Tenant ID": tenant_id,
        "Host Name": hostname,
        "Pipeline Name": project_name,
        "Runtime Parameters": runtime_params,
        "Environment": env,
        "File": filename,
        "Location": hook_name,
        "Error": str(e),
        "Traceback": error_traceback
    }

    html_body = create_html_body(error_info)
    send_email_ses(send_from, send_to, f"Pipeline Error in {project_name} - {tenant_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", html_body, mail_credentials, html=True)

def handle_error_with_context(e, context: KedroContext, hook_name: str, location: str):
    send_to = context.params["mailer"]["send_to"]
    send_from = context.params["mailer"]["send_from"]  
    mail_credentials = context._get_config_credentials()["email_access"]

    hostname = socket.gethostname()
    error_traceback = traceback.format_exc()
    tenant_id = context.params["tenant_id"]
    runtime_params = context.config_loader.runtime_params
    env = context._env
    project_name = str(context.project_path).split("/")[-1]

    error_info = {
        "Tenant ID": tenant_id,
        "Host Name": hostname,
        "Pipeline Name": project_name,
        "Runtime Parameters": runtime_params,
        "Environment": env,
        "Location": location,
        "Function": hook_name,
        "Error": str(e),
        "Traceback": error_traceback
    }

    html_body = create_html_body(error_info)
    send_email_ses(send_from, send_to, f"Pipeline Error in {project_name} - {tenant_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", html_body, mail_credentials, html=True)

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
