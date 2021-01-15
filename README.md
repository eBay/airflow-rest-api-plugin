# Airflow Plugin - API
A plugin of Apache Airflow that exposes REST endpoints for custom REST APIs. In the process of using airflow, it was found that the airflow api could not meet the business requirement, so some custom interfaces were added to the airflow plugin. 

## Requirements
- [apache-airflow](https://github.com/apache/airflow)
- [Flask-Login](https://github.com/maxcountryman/flask-login)
- [Flask-JWT-Extended](https://github.com/vimalloc/flask-jwt-extended)
- [Flask](https://github.com/pallets/flask)
- [Flask-Admin](https://github.com/flask-admin/flask-admin)
- [Flask-AppBuilder](https://github.com/dpgaspar/Flask-AppBuilder)

## Deploy plugin
1. Download plugins zip from:
```url
https://github.corp.ebay.com/linhgao/airflow-rest-api-plugin/archive/master.zip
```
2. Check the [plugins_floder](http://airflow.apache.org/docs/1.10.11/configurations-ref.html#plugins-folder) configuration in airflow.cfg. If not, please configure.
3. Unzip the plugins zip, move `rest_api_plugin.py` and `templates folder` to [plugins_floder](http://airflow.apache.org/docs/1.10.11/configurations-ref.html#plugins-folder) directory.
```bash
unzip airflow-rest-api-plugin-master.zip

cp -r airflow-rest-api-plugin-master/plugins/* {AIRFLOW_PLUGINS_FOLDER}
```
4. Start services of the airflow webserver and the airflow scheduler.
```bash
airflow webserver -p 8080
airflow scheduler
```

## Directory structure
- **/plugins**
  - **/rest_api_plugin.py** - Airflow plugins, achieve some custom interface
  - **/templates** - Airflow plugins front-end page, integrated on airflow ui
- **/tests** - Airflow plugins unittests
- **/LICENSE** - airflow-rest-api-plugin license

## Configuration
Airflow does not have permission authentication by `default`, and the following configuration can `be ignored`. If you need to add RBAC authorization verification, please refer to the following configuration.
### RBAC
Airflow supports [RBAC](http://airflow.apache.org/docs/1.10.11/security.html?highlight=ldap#rbac-ui-security) function since version 1.10.4.<br>
RBAC means Role-Based Access Control.In RBAC, permissions are associated with roles, and users get the permissions of these roles by becoming members of appropriate roles. This greatly simplifies the management of permissions. In this way, the management is hierarchical, and permissions are assigned to roles, and roles are assigned to users. Such permissions are clearly designed and easy to manage.<br>
In RBAC, Permission verification combines JWT(JSON Web Token).

#### Enable airflow RBAC
1. Set `rbac = True` in `airflow.cfg`
2. Run `airflow initdb` command which initialize some related tables of rbac, such as ab_user, ab_role, ab_permission, etc.
3. When airflow rbac is enabled for the first time, run airflow [create_user](https://airflow.apache.org/docs/stable/cli-ref#create_user) command which add users to ab_user, and specify the role through -r. Examples:
```bash
airflow create_user --role Admin --username linhgao --email linhgao@ebay.com --firstname linhua --lastname gao --password airflow
```
4. Use username and password to login the airflow web UI. 

#### Enable JWT Auth tokens
Plugin enables JWT Token based authentication for Airflow versions 1.10.4 or higher when RBAC support is enabled.
##### Generating the JWT access token
```bash
curl -XPOST http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/api/v1/security/login -H "Content-Type: application/json" -d '{"username":"username", "password":"password", "refresh":true, "provider": "db"}'
```
##### Examples:
```bash
curl -X POST http://localhost:8080/api/v1/security/login -H "Content-Type: application/json" -d '{"username":"linhgao", "password":"airflow", "refresh":true, "provider": "db"}'
```
##### Sample response which includes access_token and refresh_token.
```json
{
 "access_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MDQyMTc4MzgsIm5iZiI6MTYwNDIxNzgzOCwianRpIjoiMTI4ZDE2OGQtMTZiOC00NzU0LWJiY2EtMTEyN2E2ZTNmZWRlIiwiZXhwIjoxNjA0MjE4NzM4LCJpZGVudGl0eSI6MSwiZnJlc2giOnRydWUsInR5cGUiOiJhY2Nlc3MifQ.xSWIE4lR-_0Qcu58OiSy-X0XBxuCd_59ic-9TB7cP9Y",
 "refresh_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MDQyMTc4MzgsIm5iZiI6MTYwNDIxNzgzOCwianRpIjoiZjA5NTNkODEtNWY4Ni00YjY0LThkMzAtYzg5NTYzMmFkMTkyIiwiZXhwIjoxNjA2ODA5ODM4LCJpZGVudGl0eSI6MSwidHlwZSI6InJlZnJlc2gifQ.VsiRr8_ulCoQ-3eAbcFz4dQm-y6732QR6OmYXsy4HLk"
}
```
By default, JWT access token is valid for 15 mins and refresh token is valid for 30 days. You can renew the access token with the help of refresh token as shown below.

##### Renewing the Access Token
```bash
curl -X POST "http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/api/v1/security/refresh" -H 'Authorization: Bearer <refresh_token>'
```
##### Examples:
```bash
curl -X POST "http://localhost:8080/api/v1/security/refresh" -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MDQyMTc4MzgsIm5iZiI6MTYwNDIxNzgzOCwianRpIjoiZjA5NTNkODEtNWY4Ni00YjY0LThkMzAtYzg5NTYzMmFkMTkyIiwiZXhwIjoxNjA2ODA5ODM4LCJpZGVudGl0eSI6MSwidHlwZSI6InJlZnJlc2gifQ.VsiRr8_ulCoQ-3eAbcFz4dQm-y6732QR6OmYXsy4HLk'
```
##### sample response returns the renewed access token as shown below.
```json
{
 "access_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MDQyODQ2OTksIm5iZiI6MTYwNDI4NDY5OSwianRpIjoiZDhhN2IzMmYtMWE5Zi00Y2E5LWFhM2ItNDEwMmU3ZmMyMzliIiwiZXhwIjoxNjA0Mjg1NTk5LCJpZGVudGl0eSI6MSwiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIn0.qY2e-bNSgOY-YboinOoGqLfKX9aQkdRjo025mZwBadA"
}
```
Working with the rest_api_plugin and JWT Auth tokens.

#### Enable API request with JWT
##### If the Authorization header is not added in the api request，response error:
```json
{"msg":"Missing Authorization Header"}
```
##### Pass the additional Authorization:Bearer <access_token> header in the rest API request.
Examples:
```bash
curl -X GET -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MDQyODQ2OTksIm5iZiI6MTYwNDI4NDY5OSwianRpIjoiZDhhN2IzMmYtMWE5Zi00Y2E5LWFhM2ItNDEwMmU3ZmMyMzliIiwiZXhwIjoxNjA0Mjg1NTk5LCJpZGVudGl0eSI6MSwiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIn0.qY2e-bNSgOY-YboinOoGqLfKX9aQkdRjo025mZwBadA' http://localhost:8080/rest_api/api\?api\=dag_state\&dag_id\=dag_test\&run_id\=manual__2020-10-28T17%3A36%3A28.838356%2B00%3A00
```

## Using the REST API
Once you deploy the plugin and restart the webserver, you can start to use the REST API. Bellow you will see the endpoints that are supported. In addition, you can also interact with the REST API from the Airflow Webserver. When you reload the page, you will see a link under the Admin tab called "REST API". Clicking on the link will navigate you to the following URL:<br>
`http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/`<br>

**Note:** If enable RBAC, `http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/rest_api/`<br>
This web page will show the Endpoints supported and provide a form for you to test submitting to them.

- [deploy_dag](#deploy_dag)
- [refresh_all_dags](#refresh_all_dags)
- [delete_dag](#delete_dag)
- [upload_file](#upload_file)
- [dag_state](#dag_state)
- [task_instance_detail](#task_instance_detail)
- [restart_failed_task](#restart_failed_task)
- [kill_running_tasks](#kill_running_tasks)
- [run_task_instance](#run_task_instance)
- [skip_task_instance](#skip_task_instance)
### ***<span id="deploy_dag">deploy_dag</span>***
##### Description:
- Deploy a new dag, and refresh dag to session.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/rest_api/api?api=deploy_dag
```
##### Method:
- POST
##### POST request Arguments:
- dag_file - file - Python file to upload and deploy.
- force (optional) - boolean - Whether to forcefully upload the file if the file already exists or not.
- pause (optional) - boolean - The DAG will be forced to be paused.
- unpause (optional) - boolean - The DAG will be forced to be unpaused.
##### Examples:
```bash
curl -X POST -H 'Content-Type: multipart/form-data' -F 'dag_file=@dag_test.py' -F 'force=on' -F 'unpause=true' http://localhost:8080/admin/rest_api/api?api=deploy_dag
```
##### response:
```json
{
  "message": "DAG File [<module 'module.name' from '/Users/linhgao/airflow/dags/dag_test.py'>] has been uploaded", 
  "status": "success"
}
```
### ***<span id="refresh_all_dags">refresh_all_dags</span>***
##### Description:
- Get all dags from dag_floder, refresh the dags to the session.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=refresh_all_dags
```
##### Method:
- GET
##### GET request Arguments:
- None
##### Examples:
```bash
curl -X GET http://localhost:8080/admin/rest_api/api?api=refresh_all_dags
```
##### response:
```json
{
  "message": "All DAGs are now up to date",
  "status": "success"
}
```
### ***<span id="delete_dag">delete_dag</span>***
##### Description:
- Delete dag based on dag_id.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=delete_dag&dag_id=value
```
##### Method:
- GET
##### GET request Arguments:
- dag_id - string - The id of dag.
##### Examples:
```bash
curl -X GET http://localhost:8080/admin/rest_api/api?api=delete_dag&dag_id=dag_test
```
##### response:
```json
{
  "message": "DAG [dag_test] deleted",
  "status": "success"
}
```
### ***<span id="upload_file">upload_file</span>***
##### Description:
- Upload a new File to the specified folder.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=upload_file
```
##### Method:
- POST
##### POST request Arguments:
- file - file - uploaded file.
- force (optional) - boolean - Whether to forcefully upload the file if the file already exists or not.
- path (optional) - string - The path of file.
##### Examples:
```bash
curl -X POST -H 'Content-Type: multipart/form-data' -F 'file=@dag_test.txt' -F 'force=on' http://localhost:8080/admin/rest_api/api?api=upload_file
```
##### response:
```json
{
  "message": "File [/Users/linhgao/airflow/dags/dag_test.txt] has been uploaded",
  "status": "success"
}
```
### ***<span id="dag_state">dag_state</span>***
##### Description:
- Get the status of a dag run.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=dag_state&dag_id=value&run_id=value
```
##### Method:
- GET
##### GET request Arguments:
- dag_id - string - The id of dag.
- run_id - string - The id of the dagRun.
##### Examples:
```bash
curl -X GET http://localhost:8080/admin/rest_api/api?api=dag_state&dag_id=dag_test&run_id=manual__2020-10-28T16%3A15%3A19.427214%2B00%3A00
```
##### response:
```json
{
  "state": "success",
  "startDate": "2020-10-28T16:15:19.436693+0000",
  "endDate": "2020-10-28T16:21:36.245696+0000",
  "status": "success"
}
```
### ***<span id="task_instance_detail">task_instance_detail</span>***
##### Description:
- Get the detail info of a task instance.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=task_instance_detail&dag_id=value&run_id=value&task_id=value
```
##### Method:
- GET
##### GET request Arguments:
- dag_id - string - The id of dag.
- run_id - string - The id of the dagRun.
- task_id - string - The id of the task.
##### Examples:
```bash
curl -X GET http://localhost:8080/admin/rest_api/api?api=task_instance_detail&dag_id=dag_test&run_id=manual__2020-10-28T16%3A31%3A17.247035%2B00%3A00&task_id=task_test
```
##### response:
```json
{
  "taskId": "task_test",
  "dagId": "dag_test",
  "state": "success",
  "tryNumber": null,
  "maxTries": null,
  "startDate": "2020-10-28T16:31:57.882329+0000",
  "endDate": "2020-10-28T16:31:57.882329+0000",
  "duration": null,
  "status": "success"
}
```
### ***<span id="restart_failed_task">restart_failed_task</span>***
##### Description:
- Restart failed tasks with downstream.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=restart_failed_task&dag_id=value&run_id=value
```
##### Method:
- GET
##### GET request Arguments:
- dag_id - string - The id of dag.
- run_id - string - The id of the dagRun.
##### Examples:
```bash
curl -X GET http://localhost:8080/admin/rest_api/api?api=restart_failed_task&dag_id=dag_test&run_id=manual__2020-10-28T16%3A31%3A17.247035%2B00%3A00
```
##### response:
```json
{
  "failed_task_count": 2,
  "clear_task_count": 6,
  "status": "success"
}
```
### ***<span id="kill_running_tasks">kill_running_tasks</span>***
##### Description:
- Kill running tasks that status in ['none', 'running'].
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=kill_running_tasks&dag_id=value&run_id=value&task_id=value
```
##### Method:
- GET
##### GET request Arguments:
- dag_id - string - The id of dag.
- run_id - string - The id of the dagRun.
- task_id - string - If task_id is none, kill all tasks, else kill one task.
##### Examples:
```bash
curl -X GET http://localhost:8080/admin/rest_api/api?api=kill_running_tasks&dag_id=dag_test&run_id=manual__2020-10-28T16%3A31%3A17.247035%2B00%3A00&task_id=task_test
```
##### response:
```json
{
  "status": "success"
}
```
### ***<span id="run_task_instance">run_task_instance</span>***
##### Description:
- Create dagRun, and run some tasks, other task skip.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=run_task_instance
```
##### Method:
- POST
##### POST request Arguments:
- dag_id - string - The id of dag.
- run_id - string - The id of the dagRun.
- tasks - string - The id of the tasks, Multiple tasks are split by comma.
- conf - string - Conf of creating dagRun.
##### Examples:
```bash
curl -X POST -F 'dag_id=dag_test' -F 'run_id=manual__2020-10-28T17:36:28.838356+00:00' -F 'tasks=task_test_3,task_test_4,task_test_6' http://localhost:8080/admin/rest_api/api?api=run_task_instance
```
##### response:
```json
{
  "execution_date": "2020-10-28T17:39:14.941060+0000",
  "status": "success"
}
```
### ***<span id="skip_task_instance">skip_task_instance</span>***
##### Description:
- Skip one task instance and downstream task.
##### Endpoint:
```text
http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/admin/rest_api/api?api=skip_task_instance&dag_id=value&run_id=value&task_id=value
```
##### Method:
- GET
##### GET request Arguments:
- dag_id - string - The id of dag.
- run_id - string - The id of the dagRun.
- task_id - string - The id of the task.
##### Examples:
```bash
curl -X GET http://localhost:8080/admin/rest_api/api?api=skip_task_instance&dag_id=dag_test&run_id=manual__2020-10-28T17%3A43%3A10.053716%2B00%3A00&task_id=task_test_2
```
##### response:
```json
{
  "status": "success"
}
```

## Run UT
In order to view the ut coverage, you need to install `coverage`, which can be installed by the following command: 
```bash
pip install coverage
```
Run the `tests/test_rest_api_plugins.py` file，generate a `.coverage` file
```bash
coverage run tests/test_rest_api_plugins.py
```
Generate html format file
```bash
coverage html
```
Open the `htmlcov/index.html` file with a browser to view the coverage of ut

## Contributing to the Project
Bugs and new features should be submitted using Github issues. Please include with a detailed description and the expected behaviour. If you would like to submit a change yourself do the following steps.
1. Fork it.
2. Create a branch (git checkout -b fix-for-that-thing)
3. Commit a failing test (git commit -am "adds a failing test to demonstrate that thing")
4. Commit a fix that makes the test pass (git commit -am "fixes that thing")
5. Push to the branch (git push origin fix-for-that-thing)
6. Open a [Pull Request](github repo)

Please keep your branch up to date by rebasing upstream changes from master.

## Important links
- [Airflow configuration documentation](https://airflow.apache.org/docs/stable/configurations-ref.html)
- Contact email
  - sky - `lliu12@ebay.com`
  - linhua - `linhgao@ebay.com`

## FAQ
#### Why use Product?
Achieve airflow custom interface, make up for the lack of flexibility of airflow official interface, and meet business needs at the same time

[CONTRIBUTING](CONTRIBUTING.md)

[LICENCE](LICENCE.md)

