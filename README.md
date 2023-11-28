# MLflow Artifact Store Plugin: Leveraging Flexible Engine Object Storage

This repository offers an MLflow store plugin, enabling the utilization of [Flexible Engine](https://www.orange-business.com/en/solutions/cloud/flexible-engine) Object Storage as the primary artifact store for MLflow.

## Implementation overview

* `flexibleenginestoreplugin`: this package includes the `FlexibleEngineOSSArtifactRepository` class that is used to read and write artifacts from Flexible Engine Object Storage.
* `setup.py` file defines entrypoints that tell MLflow to automatically associate the `fe-oss` URIs with the `FlexibleEngineOSSArtifactRepository` implementation when the `flexibleenginestoreplugin` library is installed. The entrypoints are configured as follows:

```
entry_points={
        "mlflow.artifact_repository": [
            "fe-oss=flexibleenginestoreplugin.store.artifact.flexible_engine_oss_artifact_repo:FlexibleEngineOSSArtifactRepository"
        ]
```

# Usage

To store artifacts in Flexible Engine Object Storage, specify a URI of the form ``fe-oss://<bucket>/<path>``.
This plugin expects Flexible Engine Storage access credentials in the
``MLFLOW_FE_OSS_ENDPOINT_URL``, ``MLFLOW_FE_ACCESS_KEY_ID`` and ``MLFLOW_FE_SECRET_KEY`` environment variables,
so you must set these variables on both your client
application and your MLflow tracking server. Finally, you must install [OBS Python SDK]([Help Center (orange-business.com)](https://docs.prod-cloud-ocb.orange-business.com/sdk-python-devg/obs/en-us_topic_0142798482.html)) separately (on both your client and the server) to access Flexible Engine OSS Storage
