from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='flexibleenginestoreplugin',
    version='1.0.0',
    description='Plugin that provides Flexible engine oss Artifact Store functionality for MLflow',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Jatinder Singh',
    author_email='jatinder1.singh@orange.com',
    url="",
    packages=find_packages(),
    install_requires=[
        'mlflow',
        #'eSDK_Storage_OBS_Python'
    ],
    entry_points={
        "mlflow.artifact_repository": [
            "fe-oss=flexibleenginestoreplugin.store.artifact.flexible_engine_oss_artifact_repo:FlexibleEngineOSSArtifactRepository"
        ]
    },
)
