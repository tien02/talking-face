from minio import Minio
from minio.error import S3Error

from config.data import data_settings


class MinioClient:
    client = Minio(
        endpoint=data_settings.MINIO_HOST,
        access_key=data_settings.MINIO_USER_NAME,
        secret_key=data_settings.MINIO_USER_PWD,
        secure=False,
    )

    def upload(
        self, bucket_name:str, local_path:str, remote_path:str, content_type:str
    ):
        try:
            self._ensure_bucket_exists(bucket_name=bucket_name)
            self.client.fput_object(
                bucket_name=bucket_name,
                object_name=remote_path,
                file_path=local_path,
                content_type=content_type,
            )

        except S3Error as e:
            raise Exception(f"Error uploading {local_path} to {remote_path}: {str(e)}")

    def download(self, bucket_name:str, object_name:str):
        try:
            response = self.client.get_object(bucket_name, object_name)
            file_data = response.read()
            return file_data
        except S3Error as e:
            raise Exception(f"Error downloading file {object_name}: {str(e)}")\
    
    def _ensure_bucket_exists(self, bucket_name:str):
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            