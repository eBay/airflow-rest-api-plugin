# Contributing to airflow-rest-api-plugin
Bugs and new features should be submitted using Github issues. Please include with a detailed description and the expected behaviour. If you would like to submit a change yourself do the following steps.
1. Fork it.
2. Create a branch (git checkout -b fix-for-that-thing)
3. Commit a failing test (git commit -am "adds a failing test to demonstrate that thing")
4. Commit a fix that makes the test pass (git commit -am "fixes that thing")
5. Push to the branch (git push origin fix-for-that-thing)
6. Open a [Pull Request](github repo)

Please keep your branch up to date by rebasing upstream changes from master.

## Local development
First, to make sure that the required [dependencies](https://github.corp.ebay.com/beo/airflow-rest-api-plugin#requirements) have been successfully installed. The dependencies can be installed by the following command:
```bash
pip install [package]
```

## Deploy plugin
1. Check the [plugins_floder](http://airflow.apache.org/docs/1.10.11/configurations-ref.html#plugins-folder) configuration in ~/airflow/airflow.cfg. If not, please configure.
2. Copy `rest_api_plugin.py` and `templates folder` to [plugins_floder](http://airflow.apache.org/docs/1.10.11/configurations-ref.html#plugins-folder) directory.
```bash
cp -r airflow-rest-api-plugin/plugins/ {PLUGINS_FOLDER}
```
3. Start services of the airflow webserver and the airflow scheduler.
```bash
airflow webserver -p 8080
airflow scheduler
```

## Tests
1. Enter the airflow home page through the following url:
```url
http://localhost:8080/admin/
```
2. Enter the airflow rest api plugins page through the following url: 
```url
http://localhost:8080/admin/rest_api/
```
You can also enter the page through `Admin - REST API Plugins` on the upper navigation bar

- tips: 
  - If you add a new interface, you need to add the interface information in the `apis_metadata` list of the `rest_api_plugin.py` file, otherwise the new interface you added cannot be displayed on the ui.
  - Every time you modify the `rest_api_plugin.py` file, you need to restart the airflow webserver service. You can kill the service through `Crtl + C`, and then start it through the `airflow webserver -p 8080` command.