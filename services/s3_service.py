"""
services/s3_service.py

Lapisan service yang membungkus semua interaksi dengan AWS S3 memakai boto3.
Di aplikasi ini S3 dipakai sebagai "Cloud Vault": tempat menyimpan foto kondisi
unit PS3 dan bukti pembayaran, terorganisir per folder transaksi rental.
Fungsinya sengaja dibuat generik (list/upload/delete/rename/preview) supaya
benar-benar berfungsi sebagai modul MANAJEMEN S3, bukan sekadar upload sekali pakai.
"""

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError


class S3ServiceError(Exception):
    pass


class S3Service:
    def __init__(self, config):
        self.config = config
        session_kwargs = {
            "aws_access_key_id": config.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": config.AWS_SECRET_ACCESS_KEY,
            "region_name": config.AWS_REGION,
        }
        if config.AWS_SESSION_TOKEN:
            session_kwargs["aws_session_token"] = config.AWS_SESSION_TOKEN

        self.session = boto3.session.Session(**session_kwargs)

        client_kwargs = {}
        endpoint_url = getattr(config, "AWS_ENDPOINT_URL", "")
        if endpoint_url:
            # LocalStack (dan sebagian besar S3-compatible storage) butuh
            # endpoint_url kustom + path-style addressing (bukan virtual-hosted).
            client_kwargs["endpoint_url"] = endpoint_url
            client_kwargs["config"] = BotoConfig(s3={"addressing_style": "path"})

        self.client = self.session.client("s3", **client_kwargs)
        self.bucket = config.VAULT_BUCKET
        self.using_localstack = bool(endpoint_url)

    # ------------------------------------------------------------------
    def ensure_bucket_exists(self):
        """Membuat bucket vault otomatis jika belum ada (dipanggil saat startup)."""
        if not self.bucket:
            return False
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except ClientError:
            try:
                if self.config.AWS_REGION == "us-east-1":
                    self.client.create_bucket(Bucket=self.bucket)
                else:
                    self.client.create_bucket(
                        Bucket=self.bucket,
                        CreateBucketConfiguration={"LocationConstraint": self.config.AWS_REGION},
                    )
                return True
            except ClientError:
                return False
        except (NoCredentialsError, EndpointConnectionError):
            return False

    def get_bucket_info(self):
        total_size = 0
        total_objects = 0
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket):
                for obj in page.get("Contents", []):
                    total_size += obj["Size"]
                    total_objects += 1
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal mengambil info vault: {e}")

        return {"bucket": self.bucket, "region": self.config.AWS_REGION,
                "total_objects": total_objects, "total_size": total_size}

    # ------------------------------------------------------------------
    # OBJECTS / FILES & FOLDERS
    # ------------------------------------------------------------------
    def list_objects(self, prefix=""):
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            folders, files = [], []
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix, Delimiter="/"):
                for cp in page.get("CommonPrefixes", []):
                    folder_key = cp["Prefix"]
                    folder_name = folder_key[len(prefix):].rstrip("/")
                    if folder_name:
                        folders.append({"name": folder_name, "key": folder_key})
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key == prefix:
                        continue
                    name = key[len(prefix):]
                    if not name:
                        continue
                    files.append({
                        "name": name, "key": key,
                        "size": obj["Size"], "last_modified": obj["LastModified"],
                    })
            return folders, files
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal membaca isi vault: {e}")

    def create_folder(self, prefix, folder_name):
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        key = f"{prefix}{folder_name}/"
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=b"")
            return key
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal membuat folder: {e}")

    def upload_file(self, prefix, file_obj, filename):
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        key = f"{prefix}{filename}"
        try:
            self.client.upload_fileobj(file_obj, self.bucket, key)
            return key
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal mengunggah file '{filename}': {e}")

    def delete_object(self, key):
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal menghapus objek: {e}")

    def delete_folder(self, prefix):
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            objects_to_delete = []
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    objects_to_delete.append({"Key": obj["Key"]})
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i + 1000]
                self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": batch})
            return True
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal menghapus folder: {e}")

    def rename_object(self, old_key, new_key):
        try:
            self.client.copy_object(Bucket=self.bucket, CopySource={"Bucket": self.bucket, "Key": old_key}, Key=new_key)
            self.client.delete_object(Bucket=self.bucket, Key=old_key)
            return new_key
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal me-rename objek: {e}")

    def rename_folder(self, old_prefix, new_prefix):
        if not old_prefix.endswith("/"):
            old_prefix += "/"
        if not new_prefix.endswith("/"):
            new_prefix += "/"
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=self.bucket, Prefix=old_prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
            for key in keys:
                new_key = new_prefix + key[len(old_prefix):]
                self.client.copy_object(Bucket=self.bucket, CopySource={"Bucket": self.bucket, "Key": key}, Key=new_key)
            self.delete_folder(old_prefix)
            return new_prefix
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal me-rename folder: {e}")

    def generate_presigned_url(self, key, expires_in=None):
        expires_in = expires_in or self.config.PRESIGNED_URL_EXPIRE
        try:
            url = self.client.generate_presigned_url(
                "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in,
            )
            return self._rewrite_public_host(url)
        except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
            raise S3ServiceError(f"Gagal membuat presigned URL: {e}")

    def _rewrite_public_host(self, url):
        """
        Saat aplikasi jalan di Docker Compose bersama LocalStack, boto3 memakai
        endpoint internal (mis. http://localstack:4566) yang tidak bisa diakses
        langsung oleh browser di komputer host. AWS_ENDPOINT_URL_PUBLIC dipakai
        untuk menukar host tersebut menjadi yang bisa diakses browser
        (mis. http://localhost:4566) sebelum URL dikembalikan ke halaman web.
        """
        public_endpoint = getattr(self.config, "AWS_ENDPOINT_URL_PUBLIC", "")
        internal_endpoint = getattr(self.config, "AWS_ENDPOINT_URL", "")
        if not public_endpoint or not internal_endpoint or public_endpoint == internal_endpoint:
            return url
        return url.replace(internal_endpoint, public_endpoint)

