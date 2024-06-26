# kedro-error-emailer

## Overview

The Kedro Pipeline Error Notifier is a sophisticated error handling and notification system designed to integrate seamlessly with Kedro pipelines, handling error occurring during pipeline and hooks code execution. This system ensures that critical errors during pipeline execution are promptly reported to the relevant stakeholders via email. The error notifier is highly configurable, allowing users to specify which types of errors should trigger notifications and which should be ignored.


## Key Features
* `Automatic Error Detection`: Automatically detects errors that occur during the execution of Kedro pipeline hooks.<br>

* `Email Notifications`: Sends detailed error reports via email to predefined recipients. <br>

* `Customizable Ignored Exceptions`: Allows users to specify which types of exceptions should be ignored and not trigger email notifications.<br>

* `Comprehensive Error Reports`: Generates detailed error reports that include information about the tenant ID, hostname, pipeline name, runtime parameters, environment, location, file, error message, and traceable.<br>

* `Flexible Configuration`: Configuration parameters are managed through a YAML file, making it easy to customize the behavior of the error notifier.

## Deployment
To deploy the kedro error emailer, follow these step:

### 1. Importing package

Install the `kedro_error_emailer` package by running 
```bash
pip install git+https://github.com/dodobird-ai/kedro-error-emailer.git
```
or by adding to your requirements.txt
```txt
git+https://github.com/dodobird-ai/kedro-error-emailer.git
```
<br>

### 2. Add `MailerHook` hook
In kedro `setting.py`, import `MailerHook` with 
```Python
from kedro_error_emailer import MailerHook
```
and add it to `HOOKS` list.<br>


### 3. Add `@error_handler` to existing hook
For the error handling to cover the already existing hook, a decorator should be add between the  `@hook_impl` and the function definition.
Firstly import the decorator with :
```python
from kedro_error_emailer import error_handler
```
Now add the decorator to the hook such has :
```python
@hook_impl
@error_handler
def after_context_created(self, context: KedroContext) -> None:
```
__WARNING__: Should NOT be apply on `before_node_run`, `on_node_error` or `after_node_run` hook to avoid duplicated email, these hook are cover by the previously add `MailerHook` hook. A error will be raise if apply on these hook.

### 4. Parameters setup
the following parameters should be add to `parameters.yml`:
```yaml
error_mailer:
  email:
    send_from: sender_email@dodobird.ai
    send_to:
      - to_send@dodobird.ai
      - to_send2@dodobird.ai
  ignored_exceptions:
    - EmptyDfException
    - TypeError
  additional_info:
    tenant_id:  "${globals:tenant_id}"
    tenant_name: "${globals:tenant_name}"
    marketing_automation_run:  "${globals:marketing_automation_run}"
    output_type: "${user_logging.campaign_feeder_node.output_type}"
```
Parameters | Description
-------- | -------
send_from | The email address from which the error notification will be send.
send_to | A list of email addresses that will receive the error notifications.
ignored_exceptions | A list of exception type names (as strings) that should be ignored and not trigger an email notification.
additional_info | The list of elements which will be dynamically add to email. This field has for purpose to customize the email and insert information from the catalog into the email.

### 5. AWS SES email credential setup
Add to a `.env` your aws ses credentials as showed in this example:
```
MAILER_AWS_ACCESS_KEY_ID=####################
MAILER_AWS_SECRET_ACCESS_KEY=########################################
MAILER_REGION_NAME=#############
```
