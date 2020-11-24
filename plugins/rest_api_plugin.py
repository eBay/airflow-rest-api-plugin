__author__ = 'lliu12, linhgao'
__version__ = "1.0.0"

from airflow.models import DagBag, DagModel, DagRun, DAG
from airflow.plugins_manager import AirflowPlugin
from airflow import configuration
from airflow.www.app import csrf
from airflow import settings
from airflow.utils.state import State
from airflow.utils import timezone
from airflow.exceptions import TaskNotFound

from flask import Blueprint, request, jsonify, Response
from flask_admin import BaseView as AdminBaseview, expose as admin_expose
from flask_login.utils import _get_user

import airflow
import logging
import os
import socket
import json
from flask_appbuilder import expose as app_builder_expose, BaseView as AppBuilderBaseView
from flask_jwt_extended.view_decorators import jwt_required, verify_jwt_in_request

"""Location of the REST Endpoint
Note: Changing this will only effect where the messages are posted to on the web interface
and will not change where the endpoint actually resides"""
rest_api_endpoint = "/admin/rest_api/api"

# Getting Versions and Global variables
hostname = socket.gethostname()
airflow_version = airflow.__version__
rest_api_plugin_version = __version__


# Getting configurations from airflow.cfg file
airflow_webserver_base_url = configuration.get('webserver', 'BASE_URL')
airflow_dags_folder = configuration.get('core', 'DAGS_FOLDER')
rbac_authentication_enabled = configuration.getboolean("webserver", "RBAC")
store_serialized_dags = configuration.getboolean('core', 'store_serialized_dags')

if rbac_authentication_enabled:
    rest_api_endpoint = "/rest_api/api"


apis_metadata = [
    {
        "name": "deploy_dag",
        "description": "Deploy a new DAG File to the DAGs directory",
        "http_method": "POST",
        "form_enctype": "multipart/form-data",
        "arguments": [],
        "post_arguments": [
            {"name": "dag_file", "description": "Python file to upload and deploy", "form_input_type": "file",
             "required": True},
            {"name": "force", "description": "Whether to forcefully upload the file if the file already exists or not",
             "form_input_type": "checkbox", "required": False},
            {"name": "pause",
             "description": "The DAG will be forced to be paused when created.",
             "form_input_type": "checkbox", "required": False},
            {"name": "unpause",
             "description": "The DAG will be forced to be unpaused when created.",
             "form_input_type": "checkbox", "required": False}
        ]
    },
    {
        "name": "refresh_all_dags",
        "description": "Refresh all DAGs in the Web Server",
        "http_method": "GET",
        "arguments": []
    },
    {
        "name": "delete_dag",
        "description": "Delete a DAG in the Web Server from Airflow databas and filesystem",
        "http_method": "GET",
        "arguments": [
            {"name": "dag_id", "description": "The id of the dag", "form_input_type": "text", "required": True}
        ]
    },
    {
        "name": "upload_file",
        "description": "upload a new File to the specified folder",
        "http_method": "POST",
        "form_enctype": "multipart/form-data",
        "arguments": [],
        "post_arguments": [
            {"name": "file", "description": "uploaded file", "form_input_type": "file", "required": True},
            {"name": "force", "description": "Whether to forcefully upload the file if the file already exists or not",
             "form_input_type": "checkbox", "required": False},
            {"name": "path", "description": "the path of file", "form_input_type": "text", "required": False}
        ]
    },
    {
        "name": "dag_state",
        "description": "Get the status of a dag run",
        "http_method": "GET",
        "arguments": [
            {"name": "dag_id", "description": "The id of the dag", "form_input_type": "text", "required": True},
            {"name": "run_id", "description": "The id of the dagRun", "form_input_type": "text", "required": True}
        ]
    },
    {
        "name": "task_instance_detail",
        "description": "Get the detail info of a task instance",
        "http_method": "GET",
        "arguments": [
            {"name": "dag_id", "description": "The id of the dag", "form_input_type": "text", "required": True},
            {"name": "run_id", "description": "The id of the dagRun", "form_input_type": "text", "required": True},
            {"name": "task_id", "description": "The id of the task", "form_input_type": "text", "required": True}
        ]
    },
    {
        "name": "restart_failed_task",
        "description": "restart failed tasks with downstream",
        "http_method": "GET",
        "arguments": [
            {"name": "dag_id", "description": "The id of the dag", "form_input_type": "text", "required": True},
            {"name": "run_id", "description": "The id of the dagRun", "form_input_type": "text", "required": True}
        ]
    },
    {
        "name": "kill_running_tasks",
        "description": "kill running tasks that status in ['none', 'running']",
        "http_method": "GET",
        "arguments": [
            {"name": "dag_id", "description": "The id of the dag", "form_input_type": "text", "required": True},
            {"name": "run_id", "description": "The id of the dagRun", "form_input_type": "text", "required": True},
            {"name": "task_id", "description": "If task_id is none, kill all tasks, else kill one task",
             "form_input_type": "text", "required": False}
        ]
    },
    {
        "name": "run_task_instance",
        "description": "create dagRun, and run some tasks, other task skip",
        "http_method": "POST",
        "arguments": [
            {"name": "dag_id", "description": "The id of the dag", "form_input_type": "text", "required": True},
            {"name": "run_id", "description": "The id of the dagRun", "form_input_type": "text", "required": True},
            {"name": "tasks", "description": "The id of the tasks, Multiple tasks are split by (,)",
             "form_input_type": "text", "required": True},
            {"name": "conf", "description": "Conf of creating dagRun", "form_input_type": "text", "required": False}
        ]
    },
    {
        "name": "skip_task_instance",
        "description": "skip one task instance",
        "http_method": "GET",
        "arguments": [
            {"name": "dag_id", "description": "The id of the dag", "form_input_type": "text", "required": True},
            {"name": "run_id", "description": "The id of the dagRun", "form_input_type": "text", "required": True},
            {"name": "task_id", "description": "The id of the task", "form_input_type": "text", "required": True}
        ]
    }
]


# Function used to validate the JWT Token
def jwt_token_secure(func):
    def jwt_secure_check(arg):
        logging.info("Rest_API_Plugin.jwt_token_secure() called")
        if _get_user().is_anonymous is False and rbac_authentication_enabled is True:
            return func(arg)
        elif rbac_authentication_enabled is False:
            return func(arg)
        else:
            verify_jwt_in_request()
            return jwt_required(func(arg))

    return jwt_secure_check


class ApiResponse:
    def __init__(self):
        pass

    STATUS_OK = 200
    STATUS_BAD_REQUEST = 400
    STATUS_UNAUTHORIZED = 401
    STATUS_NOT_FOUND = 404
    STATUS_SERVER_ERROR = 500

    @staticmethod
    def standard_response(status, response_obj):
        json_data = json.dumps(response_obj)
        resp = Response(json_data, status=status, mimetype='application/json')
        return resp

    @staticmethod
    def success(response_obj={}):
        response_obj['status'] = 'success'
        return ApiResponse.standard_response(ApiResponse.STATUS_OK, response_obj)

    @staticmethod
    def error(status, error):
        return ApiResponse.standard_response(status, {
            'error': error
        })

    @staticmethod
    def bad_request(error):
        return ApiResponse.error(ApiResponse.STATUS_BAD_REQUEST, error)

    @staticmethod
    def not_found(error='Resource not found'):
        return ApiResponse.error(ApiResponse.STATUS_NOT_FOUND, error)

    @staticmethod
    def unauthorized(error='Not authorized to access this resource'):
        return ApiResponse.error(ApiResponse.STATUS_UNAUTHORIZED, error)

    @staticmethod
    def server_error(error='An unexpected problem occurred'):
        return ApiResponse.error(ApiResponse.STATUS_SERVER_ERROR, error)


class ResponseFormat:
    def __init__(self):
        pass

    @staticmethod
    def format_dag_run_state(dag_run):
        return {
            'state': dag_run.get_state(),
            'startDate': (None if not dag_run.start_date else dag_run.start_date.strftime("%Y-%m-%dT%H:%M:%S.%f%z")),
            'endDate': (None if not dag_run.end_date else dag_run.end_date.strftime("%Y-%m-%dT%H:%M:%S.%f%z"))
        }

    @staticmethod
    def format_dag_task(task_instance):
        return {
            'taskId': task_instance.task_id,
            'dagId': task_instance.dag_id,
            'state': task_instance.state,
            'tryNumber': (None if not task_instance._try_number else str(task_instance._try_number)),
            'maxTries': (None if not task_instance.max_tries else str(task_instance.max_tries)),
            'startDate': (
                None if not task_instance.start_date else task_instance.start_date.strftime("%Y-%m-%dT%H:%M:%S.%f%z")),
            'endDate': (
                None if not task_instance.end_date else task_instance.end_date.strftime("%Y-%m-%dT%H:%M:%S.%f%z")),
            'duration': (None if not task_instance.duration else str(task_instance.duration))
        }


def get_baseview():
    if rbac_authentication_enabled:
        return AppBuilderBaseView
    else:
        return AdminBaseview


class REST_API(get_baseview()):
    """API View which extends either flask AppBuilderBaseView or flask AdminBaseView"""

    @staticmethod
    def is_arg_not_provided(arg):
        return arg is None or arg == ""

    # Get the DagBag which has a list of all the current Dags
    @staticmethod
    def get_dagbag():
        return DagBag(dag_folder=settings.DAGS_FOLDER, store_serialized_dags=store_serialized_dags)

    @staticmethod
    def get_argument(request, arg):
        return request.args.get(arg) or request.form.get(arg)

    # '/' Endpoint where the Admin page is which allows you to view the APIs available and trigger them
    if rbac_authentication_enabled:
        @app_builder_expose('/')
        def list(self):
            logging.info("REST_API.list() called")

            # get the information that we want to display on the page regarding the dags that are available
            dagbag = self.get_dagbag()
            dags = []
            for dag_id in dagbag.dags:
                orm_dag = DagModel.get_current(dag_id)
                dags.append({
                    "dag_id": dag_id,
                    "is_active": (not orm_dag.is_paused) if orm_dag is not None else False
                })

            return self.render_template("/rest_api_plugin/index.html",
                                        dags=dags,
                                        airflow_webserver_base_url=airflow_webserver_base_url,
                                        rest_api_endpoint=rest_api_endpoint,
                                        apis_metadata=apis_metadata,
                                        airflow_version=airflow_version,
                                        rest_api_plugin_version=rest_api_plugin_version,
                                        rbac_authentication_enabled=rbac_authentication_enabled
                                        )
    else:
        @admin_expose('/')
        def index(self):
            logging.info("REST_API.index() called")

            # get the information that we want to display on the page regarding the dags that are available
            dagbag = self.get_dagbag()
            dags = []
            for dag_id in dagbag.dags:
                orm_dag = DagModel.get_current(dag_id)
                dags.append({
                    "dag_id": dag_id,
                    "is_active": (not orm_dag.is_paused) if orm_dag is not None else False
                })

            return self.render("rest_api_plugin/index.html",
                               dags=dags,
                               airflow_webserver_base_url=airflow_webserver_base_url,
                               rest_api_endpoint=rest_api_endpoint,
                               apis_metadata=apis_metadata,
                               airflow_version=airflow_version,
                               rest_api_plugin_version=rest_api_plugin_version,
                               rbac_authentication_enabled=rbac_authentication_enabled
                               )

    # '/api' REST Endpoint where API requests should all come in
    @csrf.exempt  # Exempt the CSRF token
    @admin_expose('/api', methods=["GET", "POST"])  # for Flask Admin
    @app_builder_expose('/api', methods=["GET", "POST"])  # for Flask AppBuilder
    @jwt_token_secure  # On each request
    def api(self):

        # Get the api that you want to execute
        api = self.get_argument(request, 'api')

        # Validate that the API is provided
        if self.is_arg_not_provided(api):
            logging.warning("api argument not provided")
            return ApiResponse.bad_request("API should be provided")

        api = api.strip().lower()
        logging.info("REST_API.api() called (api: " + str(api) + ")")

        # Get the api_metadata from the api object list that correcsponds to the api we want to run to get the metadata.
        api_metadata = None
        for test_api_metadata in apis_metadata:
            if test_api_metadata["name"] == api:
                api_metadata = test_api_metadata
        if api_metadata is None:
            logging.info("api '" + str(api) + "' was not found in the apis list in the REST API Plugin")
            return ApiResponse.bad_request("API '" + str(api) + "' was not found")

        # check if all the required arguments are provided
        missing_required_arguments = []
        dag_id = None
        for argument in api_metadata["arguments"]:
            argument_name = argument["name"]
            argument_value = self.get_argument(request, argument_name)
            if argument["required"]:
                if self.is_arg_not_provided(argument_value):
                    missing_required_arguments.append(argument_name)
            if argument_name == "dag_id" and argument_value is not None:
                dag_id = argument_value.strip()
        if len(missing_required_arguments) > 0:
            logging.warning("Missing required arguments: " + str(missing_required_arguments))
            return ApiResponse.bad_request("The argument(s) " + str(missing_required_arguments) + " are required")

        # Check to make sure that the DAG you're referring to, already exists.
        dag_bag = self.get_dagbag()
        if dag_id is not None and dag_id not in dag_bag.dags:
            logging.info("DAG_ID '" + str(dag_id) + "' was not found in the DagBag list '" + str(dag_bag.dags) + "'")
            return ApiResponse.bad_request("The DAG ID '" + str(dag_id) + "' does not exist")

        # Deciding which function to use based off the API object that was requested.
        # Some functions are custom and need to be manually routed to.
        if api == "deploy_dag":
            final_response = self.deploy_dag()
        elif api == "refresh_all_dags":
            final_response = self.refresh_all_dags()
        elif api == "delete_dag":
            final_response = self.delete_dag()
        elif api == "upload_file":
            final_response = self.upload_file()
        elif api == "dag_state":
            final_response = self.dag_state()
        elif api == "task_instance_detail":
            final_response = self.task_instance_detail()
        elif api == "restart_failed_task":
            final_response = self.restart_failed_task()
        elif api == "kill_running_tasks":
            final_response = self.kill_running_tasks()
        elif api == "run_task_instance":
            final_response = self.run_task_instance()
        elif api == "skip_task_instance":
            final_response = self.skip_task_instance()

        return final_response

    def deploy_dag(self):
        """Custom Function for the deploy_dag API
        Upload dag file，and refresh dag to session

        args:
            dag_file: the python file that defines the dag
            force: whether to force replace the original dag file
            pause: disabled dag
            unpause: enabled dag
        """
        logging.info("Executing custom 'deploy_dag' function")

        # check if the post request has the file part
        if 'dag_file' not in request.files or request.files['dag_file'].filename == '':
            logging.warning("The dag_file argument wasn't provided")
            return ApiResponse.bad_request("dag_file should be provided")
        dag_file = request.files['dag_file']

        force = True if self.get_argument(request, 'force') is not None else False
        logging.info("deploy_dag force upload: " + str(force))

        pause = True if self.get_argument(request, 'pause') is not None else False
        logging.info("deploy_dag in pause state: " + str(pause))

        unpause = True if self.get_argument(request, 'unpause') is not None else False
        logging.info("deploy_dag in unpause state: " + str(unpause))

        # make sure that the dag_file is a python script
        if dag_file and dag_file.filename.endswith(".py"):
            save_file_path = os.path.join(airflow_dags_folder, dag_file.filename)

            # Check if the file already exists.
            if os.path.isfile(save_file_path) and not force:
                logging.warning("File to upload already exists")
                return ApiResponse.bad_request("The file '" + save_file_path + "' already exists on host '" + hostname)

            logging.info("Saving file to '" + save_file_path + "'")
            dag_file.save(save_file_path)

        else:
            logging.warning("deploy_dag file is not a python file. It does not end with a .py.")
            return ApiResponse.bad_request("dag_file is not a *.py file")

        try:
            # import the DAG file that was uploaded
            # so that we can get the DAG_ID to execute the command to pause or unpause it
            import imp
            dag_file = imp.load_source('module.name', save_file_path)
        except Exception as e:
            warning = "Failed to get dag_file"
            logging.warning(warning)
            return ApiResponse.server_error("Failed to get dag_file")

        try:
            if dag_file is None or dag_file.dag is None:
                warning = "Failed to get dag"
                logging.warning(warning)
                return ApiResponse.server_error("DAG File [{}] has been uploaded".format(dag_file))
        except Exception:
            warning = "Failed to get dag from dag_file"
            logging.warning(warning)
            return ApiResponse.server_error("Failed to get dag from DAG File [{}]".format(dag_file))

        dag_id = dag_file.dag.dag_id
        logging.info("dag_id: " + dag_id)

        # Refresh dag into session
        dagbag = self.get_dagbag()
        dag = dagbag.get_dag(dag_id)
        session = settings.Session()
        dag.sync_to_db(session=session)
        dag_model = session.query(DagModel).filter(DagModel.dag_id == dag_id).first()
        logging.info("dag_model:" + str(dag_model))

        dag_model.set_is_paused(is_paused=not unpause)

        return ApiResponse.success({
            "message": "DAG File [{}] has been uploaded".format(dag_file)
        })

    @staticmethod
    def refresh_all_dags():
        """Custom Function for the refresh_all_dags API.
        Refresh all dags.
        """
        logging.info("Executing custom 'refresh_all_dags' function")

        try:
            session = settings.Session()
            orm_dag_list = session.query(DagModel).all()
            for orm_dag in orm_dag_list:
                if orm_dag:
                    orm_dag.last_expired = timezone.utcnow()
                    session.merge(orm_dag)
            session.commit()
        except Exception as e:
            error_message = "An error occurred while trying to Refresh all the DAGs: " + str(e)
            logging.error(error_message)
            return ApiResponse.server_error(error_message)

        return ApiResponse.success({
            "message": "All DAGs are now up to date"
        })

    def delete_dag(self):
        """Custom Function for the delete_dag API.
        Delete dag according to dag id，and delete the dag file
        """
        logging.info("Executing custom 'delete_dag' function")

        dag_id = self.get_argument(request, 'dag_id')
        logging.info("dag_id to delete: '" + str(dag_id) + "'")

        try:
            dag_full_path = airflow_dags_folder + os.sep + dag_id + ".py"

            if os.path.exists(dag_full_path):
                os.remove(dag_full_path)

            from airflow.api.common.experimental import delete_dag
            deleted_dags = delete_dag.delete_dag(dag_id, keep_records_in_log=False)
            if deleted_dags > 0:
                logging.info("Deleted dag " + dag_id)
            else:
                logging.info("No dags deleted")
        except Exception as e:
            error_message = "An error occurred while trying to delete the DAG '" + str(dag_id) + "': " + str(e)
            logging.error(error_message)
            return ApiResponse.server_error(error_message)

        return ApiResponse.success({
            "message": "DAG [{}] deleted".format(dag_id)
        })

    def upload_file(self):
        """Custom Function for the upload_file API.
        Upload files to the specified path.
        """
        logging.info("Executing custom 'upload_file' function")

        # check if the post request has the file part
        if 'file' not in request.files or request.files['file'] is None or request.files['file'].filename == '':
            logging.warning("The file argument wasn't provided")
            return ApiResponse.bad_request("file should be provided")
        file = request.files['file']

        path = self.get_argument(request, 'path')
        if path is None:
            path = airflow_dags_folder

        force = True if self.get_argument(request, 'force') is not None else False
        logging.info("deploy_dag force upload: " + str(force))

        # save file
        save_file_path = os.path.join(path, file.filename)

        # Check if the file already exists.
        if os.path.isfile(save_file_path) and not force:
            logging.warning("File to upload already exists")
            return ApiResponse.bad_request("The file '" + save_file_path + "' already exists on host '" + hostname)

        logging.info("Saving file to '" + save_file_path + "'")
        file.save(save_file_path)
        return ApiResponse.success({
            "message": "File [{}] has been uploaded".format(save_file_path)
        })

    def dag_state(self):
        """Get dag_run from session according to dag_id and run_id,
        return the state, startDate, endDate fields in dag_run

        args:
            dag_id: dag id
            run_id: the run id of dag run
        """
        logging.info("Executing custom 'dag_state' function")

        dag_id = self.get_argument(request, 'dag_id')
        run_id = self.get_argument(request, 'run_id')

        session = settings.Session()
        query = session.query(DagRun)
        dag_run = query.filter(
            DagRun.dag_id == dag_id,
            DagRun.run_id == run_id
        ).first()

        if dag_run is None:
            return ApiResponse.not_found("dag run is not found")

        res_dag_run = ResponseFormat.format_dag_run_state(dag_run)
        session.close()

        return ApiResponse.success(res_dag_run)

    def task_instance_detail(self):
        """Obtain task_instance from session according to dag_id, run_id and task_id,
        and return taskId, dagId, state, tryNumber, maxTries, startDate, endDate, duration fields in task_instance

        args:
            dag_id: dag id
            run_id: the run id of dag run
            task_id: the task id of task instance of dag
        """
        logging.info("Executing custom 'task_instance_detail' function")

        dag_id = self.get_argument(request, 'dag_id')
        run_id = self.get_argument(request, 'run_id')
        task_id = self.get_argument(request, 'task_id')

        session = settings.Session()
        query = session.query(DagRun)
        dag_run = query.filter(
            DagRun.dag_id == dag_id,
            DagRun.run_id == run_id
        ).first()

        if dag_run is None:
            return ApiResponse.not_found("dag run is not found")

        logging.info('dag_run：' + str(dag_run))

        task_instance = DagRun.get_task_instance(dag_run, task_id)

        if task_instance is None:
            return ApiResponse.not_found("dag task is not found")

        logging.info('task_instance：' + str(task_instance))

        res_task_instance = ResponseFormat.format_dag_task(task_instance)
        session.close()

        return ApiResponse.success(res_task_instance)

    def restart_failed_task(self):
        """Restart the failed task in the specified dag run.
        According to dag_id, run_id get dag_run from session,
        query task_instances that status is FAILED in dag_run,
        restart them and clear status of all task_instance's downstream of them.

        args:
            dag_id: dag id
            run_id: the run id of dag run
        """
        logging.info("Executing custom 'restart_failed_task' function")

        dagbag = self.get_dagbag()

        dag_id = self.get_argument(request, 'dag_id')
        run_id = self.get_argument(request, 'run_id')

        session = settings.Session()
        query = session.query(DagRun)
        dag_run = query.filter(
            DagRun.dag_id == dag_id,
            DagRun.run_id == run_id
        ).first()

        if dag_run is None:
            return ApiResponse.not_found("dag run is not found")

        if dag_id not in dagbag.dags:
            return ApiResponse.bad_request("Dag id {} not found".format(dag_id))

        dag = dagbag.get_dag(dag_id)

        if dag is None:
            return ApiResponse.not_found("dag is not found")

        tis = DagRun.get_task_instances(dag_run, State.FAILED)
        logging.info('task_instances: ' + str(tis))

        failed_task_count = len(tis)
        if failed_task_count > 0:
            for ti in tis:
                dag = DAG.sub_dag(
                    self=dag,
                    task_regex=r"^{0}$".format(ti.task_id),
                    include_downstream=True,
                    include_upstream=False)

                count = DAG.clear(
                    self=dag,
                    start_date=dag_run.execution_date,
                    end_date=dag_run.execution_date,
                )
                logging.info('count：' + str(count))
        else:
            return ApiResponse.not_found("dagRun don't have failed tasks")

        session.close()

        return ApiResponse.success({
            'failed_task_count': failed_task_count,
            'clear_task_count': count
        })

    def kill_running_tasks(self):
        """Stop running the specified task instance and downstream tasks.
        Obtain task_instance from session according to dag_id, run_id and task_id,
        If task_id is not empty, get task_instance with RUNNIN or NONE status from dag_run according to task_id,
          and set task_instance status to FAILED.
        If task_id is empty, get all task_instances whose status is RUNNIN or NONE from dag_run,
          and set the status of these task_instances to FAILED.

        args:
            dag_id: dag id
            run_id: the run id of dag run
            task_id: the task id of task instance of dag
        """
        logging.info("Executing custom 'kill_running_tasks' function")

        dagbag = self.get_dagbag()

        dag_id = self.get_argument(request, 'dag_id')
        run_id = self.get_argument(request, 'run_id')
        task_id = self.get_argument(request, 'task_id')

        session = settings.Session()
        query = session.query(DagRun)
        dag_run = query.filter(
            DagRun.dag_id == dag_id,
            DagRun.run_id == run_id
        ).first()

        if dag_run is None:
            return ApiResponse.not_found("dag run is not found")

        if dag_id not in dagbag.dags:
            return ApiResponse.bad_request("Dag id {} not found".format(dag_id))

        dag = dagbag.get_dag(dag_id)
        logging.info('dag: ' + str(dag))
        logging.info('dag_subdag: ' + str(dag.subdags))

        tis = []
        if task_id:
            task_instance = DagRun.get_task_instance(dag_run, task_id)
            if task_instance is None or task_instance.state not in [State.RUNNING, State.NONE]:
                return ApiResponse.not_found("task is not found or state is neither RUNNING nor NONE")
            else:
                tis.append(task_instance)
        else:
            tis = DagRun.get_task_instances(dag_run, [State.RUNNING, State.NONE])

        logging.info('tis: ' + str(tis))
        running_task_count = len(tis)

        if running_task_count > 0:
            for ti in tis:
                ti.state = State.FAILED
                ti.end_date = timezone.utcnow()
                session.merge(ti)
                session.commit()
        else:
            return ApiResponse.not_found("dagRun don't have running tasks")

        session.close()

        return ApiResponse.success()

    def run_task_instance(self):
        """Run some tasks, other tasks do not run
        According to dag_id, run_id get dag_run from session,
        Obtain the task instances that need to be run according to tasks，
        Define the status of these task instances as None,
        and define the status of other task instances that do not need to run as SUCCESS

        args:
            dag_id: dag id
            run_id: the run id of dag run
            tasks: the task id of task instance of dag, Multiple task ids are split by ','
            conf: define dynamic configuration in dag
        """
        logging.info("Executing custom 'run_task_instance' function")

        dagbag = self.get_dagbag()

        dag_id = self.get_argument(request, 'dag_id')
        run_id = self.get_argument(request, 'run_id')
        tasks = self.get_argument(request, 'tasks')
        conf = self.get_argument(request, 'conf')

        run_conf = None
        if conf:
            try:
                run_conf = json.loads(conf)
            except ValueError:
                return ApiResponse.error('Failed', 'Invalid JSON configuration')

        dr = DagRun.find(dag_id=dag_id, run_id=run_id)
        if dr:
            return ApiResponse.not_found('run_id {} already exists'.format(run_id))

        logging.info('tasks: ' + str(tasks))
        task_list = tasks.split(',')

        session = settings.Session()

        if dag_id not in dagbag.dags:
            return ApiResponse.not_found("Dag id {} not found".format(dag_id))

        dag = dagbag.get_dag(dag_id)
        logging.info('dag: ' + str(dag))

        for task_id in task_list:
            try:
                task = dag.get_task(task_id)
            except TaskNotFound:
                return ApiResponse.not_found("dag task of {} is not found".format(str(task_id)))
            logging.info('task：' + str(task))

        execution_date = timezone.utcnow()

        dag_run = dag.create_dagrun(
            run_id=run_id,
            execution_date=execution_date,
            state=State.RUNNING,
            conf=run_conf,
            external_trigger=True
        )

        tis = dag_run.get_task_instances()
        for ti in tis:
            if ti.task_id in task_list:
                ti.state = None
            else:
                ti.state = State.SUCCESS
            session.merge(ti)

        session.commit()
        session.close()

        return ApiResponse.success({
            "execution_date": (execution_date.strftime("%Y-%m-%dT%H:%M:%S.%f%z"))
        })

    def skip_task_instance(self):
        """Skip the specified task instance and downstream tasks.
        Obtain task instance from session according to dag_id, run_id and task_id,
        define the state of this task instance as SKIPPED.

        args:
            dag_id: dag id
            run_id: the run id of dag run
            task_id: the task id of task instance of dag
        """
        logging.info("Executing custom 'skip_task_instance' function")

        dag_id = self.get_argument(request, 'dag_id')
        run_id = self.get_argument(request, 'run_id')
        task_id = self.get_argument(request, 'task_id')

        session = settings.Session()
        query = session.query(DagRun)
        dag_run = query.filter(
            DagRun.dag_id == dag_id,
            DagRun.run_id == run_id
        ).first()

        if dag_run is None:
            return ApiResponse.not_found("dag run is not found")

        logging.info('dag_run：' + str(dag_run))

        task_instance = DagRun.get_task_instance(dag_run, task_id)

        if task_instance is None:
            return ApiResponse.not_found("dag task is not found")

        logging.info('task_instance：' + str(task_instance))

        task_instance.state = State.SKIPPED
        session.merge(task_instance)
        session.commit()
        session.close()

        return ApiResponse.success()


# Creating View to be used by Plugin
if rbac_authentication_enabled:
    rest_api_view = {"category": "Admin", "name": "REST API Plugin", "view": REST_API()}
else:
    rest_api_view = REST_API(category="Admin", name="REST API Plugin")

# Creating Blueprint
rest_api_bp = Blueprint(
    "rest_api_bp",
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/'
)

# Creating Blueprint
rest_api_blueprint = Blueprint(
    'rest_api_blueprint',
    __name__,
    url_prefix='/rest/api'
)


class REST_API_Plugin(AirflowPlugin):
    """Creating the REST_API_Plugin which extends the AirflowPlugin so its imported into Airflow"""
    name = "rest_api"
    operators = []
    appbuilder_views = [rest_api_view]
    flask_blueprints = [rest_api_bp, rest_api_blueprint]
    hooks = []
    executors = []
    admin_views = [rest_api_view]
    menu_links = []
