import unittest
from flask import request, Response, Flask
from flask_admin import expose, Admin
import json
from plugins.rest_api_plugin import REST_API
from airflow.www import app as application


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

        assert request.form['force'] == True
        request.form['unpause'] = True
        response = self.rest_api_plugin.deploy_dag()
        response_data = json.loads(response.get_data())
        print(response_data)

    def test_refresh_all_dags(self):
        print('test refresh_all_dags')
        response = self.rest_api_plugin.refresh_all_dags()
        response_data = json.loads(response.get_data())
        self.assertIn('status', response_data)
        actual_status = response_data.get('status')
        self.assertEqual('success', actual_status)

    def test_delete_dag(self):
        print('test delete_dag')

    def test_dag_state(self):
        print('test dag_state')
        form = dict(
            api="dag_state",
            dag_id="build_pyspark_env-0.0.1",
            run_id="manual__2020-11-14T09:43:31+0800"
        )
        response = self.client.post('/rest_api/api', data=form, follow_redirects=True)
        print(response)
        response_data = json.loads(response.get_data())
        print(response_data)