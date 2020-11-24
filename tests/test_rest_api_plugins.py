import unittest
from unittest import mock
from flask import request, Response, Flask
from airflow import settings
import json
from airflow.www import app as application
import io
import uuid
import sys
sys.path.append(r'../plugins/')
from rest_api_plugin import REST_API

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
        self.rest_api = REST_API()

    def test_deploy_dag(self):
        print('test deploy_dag')
        url = '/admin/rest_api/api'
        content = """from airflow.models import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash_operator import BashOperator

DEFAULT_TASK_ARGS = {
    'owner': 'linhgao',
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
}

dag = DAG(
    dag_id = 'dag_test',
    default_args = DEFAULT_TASK_ARGS,
    schedule_interval=None,
)

task_test_1 = BashOperator(
    task_id = 'task_test_1',
    bash_command = 'date; sleep 300; date',
    dag = dag
)"""

        content_2 = '{"str_key": "str_value"}'

        with mock.patch('airflow.models.Variable.set') as set_mock:
            set_mock.side_effect = UnicodeEncodeError

            bytes_content = io.BytesIO(bytes(content, encoding='utf-8'))

            form = dict(
                api="deploy_dag",
                dag_file=(bytes_content, 'dag_test.py'),
                force="true",
                unpause="true"
            )
            response = self.client.post(url, data=form, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual('success', actual_status)

            form_2 = dict(
                api="deploy_dag",
                force="true",
                unpause="true"
            )
            self.client.post(url, data=form_2, follow_redirects=True)

            form_4 = dict(
                api="deploy_dag",
                dag_file=(io.BytesIO(bytes(content_2, encoding='utf-8')), 'dag_test.txt'),
                force="true",
                unpause="true"
            )
            self.client.post(url, data=form_4, follow_redirects=True)

            print('test run_task_instance')
            url = '/admin/rest_api/api'
            run_id = uuid.uuid4()
            print(run_id)
            form = dict(
                api="run_task_instance",
                dag_id="dag_test",
                run_id=run_id,
                tasks="task_test_1"
            )
            response = self.client.post(url, data=form, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual("success", actual_status)

            form = dict(
                api="run_task_instance",
                dag_id="dag_test",
                run_id=run_id,
                tasks="task_test_1",
                conf={'dsafdfaf'}
            )
            self.client.post(url, data=form, follow_redirects=True)

            print('test kill_running_tasks')
            url = '/admin/rest_api/api?api=kill_running_tasks&dag_id=dag_test&run_id={}&task_id=task_test_1'.format(run_id)
            response = self.client.get(url, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual("success", actual_status)

            print('test dag_state')
            url = '/admin/rest_api/api?api=dag_state&dag_id=dag_test&run_id={}'.format(run_id)
            response = self.client.get(url, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual("success", actual_status)

            url_1 = '/admin/rest_api/api?api=dag_state&dag_id=dag_test&run_id=aaaaabbbbbbcccc'
            self.client.get(url_1, follow_redirects=True)

            print('test task_instance_detail')
            url = '/admin/rest_api/api?api=task_instance_detail&dag_id=dag_test&run_id={}&task_id=task_test_1'.format(run_id)
            response = self.client.get(url, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual("success", actual_status)

            url_2 = '/admin/rest_api/api?api=task_instance_detail&dag_id=dag_test&run_id=aaabbbbbccc&task_id=task_test_1'
            self.client.get(url_2, follow_redirects=True)

            url = '/admin/rest_api/api?api=task_instance_detail&dag_id=dag_test&run_id={}&task_id=task_test_a'.format(
                run_id)
            self.client.get(url, follow_redirects=True)

            print('test restart_failed_task')
            url = '/admin/rest_api/api?api=restart_failed_task&dag_id=dag_test&run_id={}'.format(run_id)
            response = self.client.get(url, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual("success", actual_status)

            url = '/admin/rest_api/api?api=restart_failed_task'
            self.client.get(url, follow_redirects=True)

            url = '/admin/rest_api/api?api=restart_failed_task&dag_id=dag_test'
            self.client.get(url, follow_redirects=True)

            url = '/admin/rest_api/api?api=restart_failed_task&dag_id=dag_test&run_id={}'.format(run_id)
            self.client.get(url, follow_redirects=True)

            url = '/admin/rest_api/api?api=restart_failed_task&dag_id=dag_test_failed&run_id={}'.format(run_id)
            self.client.get(url, follow_redirects=True)

            print('test skip_task_instance')
            url = '/admin/rest_api/api?api=skip_task_instance&dag_id=dag_test&run_id={}&task_id=task_test_1'.format(run_id)
            response = self.client.get(url, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual("success", actual_status)

            print('test delete_dag')
            url = '/admin/rest_api/api?api=delete_dag&dag_id=dag_test'
            response = self.client.get(url, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual("success", actual_status)

    def test_refresh_all_dags(self):
        print('test refresh_all_dags')
        response = self.rest_api.refresh_all_dags()
        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('status', response_data)
        actual_status = response_data.get('status')
        self.assertEqual('success', actual_status)

        url = '/admin/rest_api/api?api=refresh_all_dags'
        self.client.get(url, follow_redirects=True)

        with mock.patch("airflow.utils.timezone.utcnow") as utcnow_mock:
            utcnow_mock.side_effect = Exception
            self.client.get(url, follow_redirects=True)

    def test_upload_file(self):
        print('test upload_file')
        url = '/admin/rest_api/api'
        content = '{"str_key": "str_value"}'

        with mock.patch('airflow.models.Variable.set') as set_mock:
            set_mock.side_effect = UnicodeEncodeError

            bytes_content = io.BytesIO(bytes(content, encoding='utf-8'))

            form = dict(
                api="upload_file",
                file=(bytes_content, 'test.json'),
                force="true"
            )
            response = self.client.post(url, data=form, follow_redirects=True)
            response_data = json.loads(response.get_data())
            print(response_data)
            self.assertIn('status', response_data)
            actual_status = response_data.get('status')
            self.assertEqual('success', actual_status)

            form_1 = dict(
                api="upload_file",
                force="true"
            )
            self.client.post(url, data=form_1, follow_redirects=True)

    def test_api_provided(self):
        url = '/admin/rest_api/api'
        response = self.client.get(url, follow_redirects=True)

        response_data = json.loads(response.get_data())
        print(response_data)
        self.assertIn('error', response_data)
        actual_error = response_data.get('error')
        self.assertEqual('API should be provided', actual_error)

    @mock.patch("imp.load_source")
    def test_load_source(self, loadSourceMock):
        print('test deploy_dag')
        url = '/admin/rest_api/api'
        content = """from airflow.models import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash_operator import BashOperator

DEFAULT_TASK_ARGS = {
    'owner': 'linhgao',
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
}

dag = DAG(
    dag_id = 'dag_test',
    default_args = DEFAULT_TASK_ARGS,
    schedule_interval=None,
)

task_test_1 = BashOperator(
    task_id = 'task_test_1',
    bash_command = 'date; sleep 300; date',
    dag = dag
)"""

        bytes_content = io.BytesIO(bytes(content, encoding='utf-8'))

        form = dict(
            api="deploy_dag",
            dag_file=(bytes_content, 'dag_test.py'),
            force="true",
            unpause="true"
        )
        loadSourceMock.side_effect = Exception
        self.client.post(url, data=form, follow_redirects=True)

    def test_delete_dag_rm(self):
        with mock.patch("os.remove") as remove_mock:
            remove_mock.side_effect = Exception
            url = '/admin/rest_api/api?api=delete_dag&dag_id=dag_test'
            self.client.get(url, follow_redirects=True)

    def test_index(self):
        url = '/admin/rest_api/'
        self.client.get(url, follow_redirects=True)


if __name__ == '__main__':
    unittest.main()