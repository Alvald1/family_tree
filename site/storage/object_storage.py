"""Object storage adapters for private file blobs."""

import mimetypes


class S3ObjectStorage:
    def __init__(
        self,
        bucket,
        endpoint_url,
        access_key_id,
        secret_access_key,
        region_name="ru-central1",
        client=None,
    ):
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        if client is None:
            import boto3

            client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region_name,
            )
        self.client = client

    @classmethod
    def from_config(cls, config):
        if not config.enabled:
            return None
        return cls(
            bucket=config.bucket,
            endpoint_url=config.endpoint_url,
            access_key_id=config.access_key_id,
            secret_access_key=config.secret_access_key,
            region_name=config.region_name,
        )

    def put_bytes(self, key, data, content_type):
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def get_object(self, key):
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
        except Exception as error:
            if self._is_not_found(error):
                return None
            raise

        content_type = response.get("ContentType") or _guess_content_type(key)
        return {
            "data": response["Body"].read(),
            "content_type": content_type,
        }

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def _is_not_found(self, error):
        response = getattr(error, "response", {})
        code = response.get("Error", {}).get("Code")
        return code in {"404", "NoSuchKey", "NotFound"}


def _guess_content_type(key):
    content_type, _ = mimetypes.guess_type(key)
    return content_type or "application/octet-stream"
