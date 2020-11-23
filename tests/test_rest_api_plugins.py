import unittest
from unittest import mock
from flask import request, Response, Flask
from flask_admin import expose, Admin
from airflow import models
import json
from plugins.rest_api_plugin import REST_API
from airflow.www import app as application
import string
import random
import io


class TestRestApiPlugins(unittest.TestCase):

    flask = Flask(__name__)

    @classmethod
    def setUpClass(cls):
        cls.app = application.create_app(testing=True)

    def setUp(self):
        self.client = self.app.test_client()

    @classmethod
    def tearDownClass(cls):
        application.app = None

    def __init__(self, *args, **kwargs):
        super(TestRestApiPlugins, self).__init__(*args, **kwargs)
        self.rest_api_plugin = REST_API()

    def test_deploy_dag(self):
        print('test deploy_dag')
        url = '/admin/rest_api/api'
        content = """from airflow.models import DAG
                     from airflow.utils.dates import days_ago
                     from airflow.operators.bash_operator import BashOperator
                     from airflow.operators.dummy_operator import DummyOperator
                     from airflow.models import Variable
                     from datetime import datetime
                        
                     echo_workflow_schedule = Variable.get("echo_workflow_schedule", default_var=None)
                        
                     DEFAULT_TASK_ARGS = {
                         'owner': 'linhgao',
                         'start_date': days_ago(1),
                         'email_on_failure': True,
                         'email_on_retry': False,
                     }
                        
                     dag = DAG(
                         dag_id = 'dag_test',
                         default_args = DEFAULT_TASK_ARGS,
                         schedule_interval=echo_workflow_schedule,
                         user_defined_macros={
                             'current_date':datetime.now().strftime("%Y-%m-%d"),
                             'current_time':datetime.now().strftime("%Y-%m-%d")
                         }
                        
                     )
                        
                     task_test_1 = DummyOperator(
                         task_id = 'task_test_1',
                         dag = dag
                     )"""

        with mock.patch('airflow.models.Variable.set') as set_mock:
            set_mock.side_effect = UnicodeEncodeError

            try:
                # python 3+
                bytes_content = io.BytesIO(bytes(content, encoding='utf-8'))
            except TypeError:
                # python 2.7
                bytes_content = io.BytesIO(bytes(content))

            form = dict(
                api="deploy_dag",
                dag_file=(bytes_content, 'dag_test.py'),
                force="true",
                unpause="true"
            )
            response = self.client.get(url, data=form, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('error', response_data)
            actual_status = response_data.get('error')
            self.assertEqual('Failed to get dag_file', actual_status)

    def test_refresh_all_dags(self):
        print('test refresh_all_dags')
        response = self.rest_api_plugin.refresh_all_dags()
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('status', response_data)
        actual_status = response_data.get('status')
        self.assertEqual('success', actual_status)

    def test_delete_dag(self):
        print('test delete_dag')
        url = '/admin/rest_api/api?api=delete_dag&dag_id=move_data_test_v1'
        response = self.client.get(url, follow_redirects=True)
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('error', response_data)
        actual_status = response_data.get('error')
        self.assertEqual("The DAG ID 'move_data_test_v1' does not exist", actual_status)

    def test_upload_file(self):
        print('test upload_file')
        url = '/admin/rest_api/api'
        content = '{"str_key": "str_value"}'

        with mock.patch('airflow.models.Variable.set') as set_mock:
            set_mock.side_effect = UnicodeEncodeError

            try:
                # python 3+
                bytes_content = io.BytesIO(bytes(content, encoding='utf-8'))
            except TypeError:
                # python 2.7
                bytes_content = io.BytesIO(bytes(content))

            form = dict(
                api="upload_file",
                file=(bytes_content, 'test.json'),
                force="true"
            )
            response = self.client.get(url, data=form, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual('success', actual_status)

    def test_dag_state(self):
        print('test dag_state')
        url = '/admin/rest_api/api?api=dag_state&dag_id=dag_test&run_id=manual__2020-10-28T17%3A43%3A10.053716%2B00%3A00'
        response = self.client.get(url, follow_redirects=True)
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('error', response_data)
        actual_status = response_data.get('error')
        self.assertEqual("The DAG ID 'dag_test' does not exist", actual_status)

    def test_task_instance_detail(self):
        print('test task_instance_detail')
        url = '/admin/rest_api/api?api=task_instance_detail&dag_id=dag_test&run_id=manual__2020-10-28T17%3A43%3A10.053716%2B00%3A00&&task_id=task_test_1'
        response = self.client.get(url, follow_redirects=True)
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('error', response_data)
        actual_status = response_data.get('error')
        self.assertEqual("The DAG ID 'dag_test' does not exist", actual_status)

    def test_restart_failed_task(self):
        print('test restart_failed_task')
        url = '/admin/rest_api/api?api=restart_failed_task&dag_id=dag_test&run_id=manual__2020-10-28T17%3A43%3A10.053716%2B00%3A00'
        response = self.client.get(url, follow_redirects=True)
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('error', response_data)
        actual_status = response_data.get('error')
        self.assertEqual("The DAG ID 'dag_test' does not exist", actual_status)

    def test_kill_running_tasks(self):
        print('test kill_running_tasks')
        url = '/admin/rest_api/api?api=kill_running_tasks&dag_id=dag_test&run_id=manual__2020-10-28T17%3A43%3A10.053716%2B00%3A00&&task_id=task_test_1'
        response = self.client.get(url, follow_redirects=True)
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('error', response_data)
        actual_status = response_data.get('error')
        self.assertEqual("The DAG ID 'dag_test' does not exist", actual_status)

    def test_run_task_instance(self):
        print('test run_task_instance')
        url = '/admin/rest_api/api'
        s = string.digits + string.ascii_letters
        form = dict(
            api="run_task_instance",
            dag_id="dag_test",
            run_id=random.sample(s, 16),
            tasks="task_test_1"
        )
        response = self.client.get(url, data=form, follow_redirects=True)
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('error', response_data)
        actual_status = response_data.get('error')
        self.assertEqual("The DAG ID 'dag_test' does not exist", actual_status)

    def test_skip_task_instance(self):
        print('test skip_task_instance')
        url = '/admin/rest_api/api?api=skip_task_instance&dag_id=dag_test&run_id=manual__2020-10-28T17%3A43%3A10.053716%2B00%3A00&&task_id=task_test_1'
        response = self.client.get(url, follow_redirects=True)
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('error', response_data)
        actual_status = response_data.get('error')
        self.assertEqual("The DAG ID 'dag_test' does not exist", actual_status)