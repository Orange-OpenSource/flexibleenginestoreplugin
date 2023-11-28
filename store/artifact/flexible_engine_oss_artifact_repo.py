# This library is under the 3-Clause BSD License
#
# Copyright (c) 2023-2024,  Orange
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of Orange nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL ORANGE BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Software Name: Flexibleenginestoreplugin
#
# Author: Jatinder Singh <Jatinder1.singh@orange.com>
#
# Software description: This is a plugin module for MLflow artifact repository
# to extend the support of Mlflow to store artifact at flexible engine object
# store service(OSS)


# Import the module.
import posixpath
import os
from six.moves import urllib

from com.obs.client.obs_client import ObsClient
from mlflow.entities import FileInfo
from mlflow.exceptions import MlflowException
from mlflow.store.artifact.artifact_repo import ArtifactRepository
from mlflow.utils.file_utils import relative_path_to_artifact_path



class FlexibleEngineOSSArtifactRepository(ArtifactRepository):
    """Stores artifacts on FE OSS."""

    def __init__(self, artifact_uri):
        """__init__."""
        self.oss_endpoint_url = os.environ.get('MLFLOW_FE_OSS_ENDPOINT_URL')
        super().__init__(artifact_uri)
        self._access_key_id = os.environ.get('MLFLOW_FE_ACCESS_KEY_ID')
        self._secret_access_key = os.environ.get('MLFLOW_FE_SECRET_KEY')
        assert self.oss_endpoint_url, 'please set MLFLOW_OSS_ENDPOINT_URL'
        assert self._access_key_id, 'please set MLFLOW_OSS_KEY_ID'
        assert self._secret_access_key, 'please set MLFLOW_OSS_KEY_SECRET'
        self.bucket_name = None
        self.is_plugin = True

    def _get_obs_client(self):
        """To get FE OSS client."""
        return ObsClient(
            access_key_id=self._access_key_id,
            secret_access_key=self._secret_access_key,
            server=self.oss_endpoint_url
        )

    @staticmethod
    def parse_oss_uri(uri):
        """Parse an OSS URI, returning (bucket, path)."""
        parsed = urllib.parse.urlparse(uri)
        if parsed.scheme != "fe-oss":
            raise RuntimeError(f"Not an FE OSS URI: {uri}")
        path = parsed.path
        if path.startswith('/'):
            path = path[1:]
        return parsed.netloc, path

    def _get_oss_bucket(self, bucket):
        """Get the existing bucket or create the bucket."""
        if bucket is not None:
            self.bucket_name = bucket
            return self.bucket_name
        obs_client = self._get_obs_client()
        self.bucket_name = obs_client.createBucket(bucket)
        return self.bucket_name

    def _upload_file(self, obs_client, local_file, bucket, key):
        """To update the file in FE OSS."""
        obs_client = self._get_obs_client()
        resp = obs_client.uploadFile(bucket, key, uploadFile=local_file)
        if resp.status < 300:
            print('requestId:', resp.requestId)
        else:
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)

    def log_artifact(self, local_file, artifact_path=None):
        """To log a artifact in FE OSS."""
        (bucket, dest_path) = self.parse_oss_uri(self.artifact_uri)
        if artifact_path:
            dest_path = posixpath.join(dest_path, artifact_path)
        dest_path = posixpath.join(dest_path, os.path.basename(local_file))
        self._get_oss_bucket(bucket)
        self._upload_file(
            obs_client=self._get_obs_client(),
            local_file=local_file,
            bucket=self.bucket_name,
            key=dest_path
        )

    def log_artifacts(self, local_dir, artifact_path=None):
        """To log the multiple artifact."""
        (bucket, dest_path) = self.parse_oss_uri(self.artifact_uri)
        if artifact_path:
            dest_path = posixpath.join(dest_path, artifact_path)
        self._get_oss_bucket(bucket)

        obs_client = self._get_obs_client()
        local_dir = os.path.abspath(local_dir)
        for root, _, filenames in os.walk(local_dir):
            upload_path = dest_path
            if root != local_dir:
                rel_path = os.path.relpath(root, local_dir)
                rel_path = relative_path_to_artifact_path(rel_path)
                upload_path = posixpath.join(dest_path, rel_path)
            for file_name in filenames:
                self._upload_file(
                    obs_client=obs_client,
                    local_file=os.path.join(root, file_name),
                    bucket=self.bucket_name,
                    key=posixpath.join(upload_path, file_name),
                )

    def list_artifacts(self, path=None):
        """To list artifacts."""
        (bucket, artifact_path) = self.parse_oss_uri(self.artifact_uri)
        dest_path = artifact_path
        if path:
            dest_path = posixpath.join(dest_path, path)
        infos = []
        prefix = dest_path + "/" if dest_path else ""
        obs_client = self._get_obs_client()
        results = obs_client.listObjects(bucketName=bucket,
                                        prefix=prefix,
                                        delimiter="/")["body"]
        for obj in results.get('contents', []):
            # is file
            file_path = obj.get("key")
            file_rel_path = posixpath.relpath(path=file_path,
                                            start=artifact_path)
            file_size = obj.size
            infos.append(FileInfo(file_rel_path, False, file_size))
        for subdir_path in results.get('commonPrefixs', []):
            # is dir
            subdir_path = subdir_path.get('prefix')
            subdir_rel_path = posixpath.relpath(path=subdir_path,
                                            start=artifact_path)
            infos.append(FileInfo(subdir_rel_path, True, None))
        return sorted(infos, key=lambda f: f.path)

    def _download_file(self, remote_file_path, local_path):
        """ To download the file """
        (bucket, oss_root_path) = self.parse_oss_uri(self.artifact_uri)
        oss_full_path = posixpath.join(oss_root_path, remote_file_path)
        obs_client = self._get_obs_client()
        resp = obs_client.downloadFile(bucket,
                                       objectKey=oss_full_path,
                                       downloadFile=local_path)
        if resp.status < 300:
            print('requestId:', resp.requestId)
        else:
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)

    def delete_artifacts(self, artifact_path=None):
        """ To delete the artifact is comment out."""
        raise MlflowException('Not implemented yet')
