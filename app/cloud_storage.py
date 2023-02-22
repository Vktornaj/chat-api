import boto3
from botocore.exceptions import ClientError


class CloudStorage():

    def __init__(self, public_key: str, secret_key: str, bucket_name: str, region_name: str) -> None:
        self.bucket_name = bucket_name
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=public_key, 
            aws_secret_access_key=secret_key,
            config=boto3.session.Config(region_name=region_name),
        )


    def upload_file(self, cloud_path: str, local_path_or_file):
        if type(local_path_or_file) is str:
            res = self.s3.upload_file(local_path_or_file, self.bucket_name, cloud_path)
        else:
            res = self.s3.upload_fileobj(local_path_or_file, self.bucket_name, cloud_path)
        return res


    def download_file(self, cloud_path: str, local_path: str):
        return self.s3.download_file(self.bucket_name, cloud_path, local_path)


    def delete_file(self, cloud_path: str):
        return self.s3.delete_object(Bucket=self.bucket_name, Key=cloud_path)


    def list_files(self, cloud_path: str | None = "") -> list[str]:
        res = self.s3.list_objects(Bucket=self.bucket_name, Prefix=cloud_path) \
            .get("Contents")
        if res is not None:
            return [ object_.get("Key") for object_ in res]
        return []

   
    def list_dirs(self, cloud_path: str | None = ""):
        res = self.s3.list_objects(
            Bucket=self.bucket_name, 
            Prefix=cloud_path, 
            Delimiter='/'
        ).get("Contents")
        if res is not None:
            return [ object_.get("Key") for object_ in res]
        return []


    def delete_dir(self, dir_path: str):
        return [
            self.delete_file(cloud_path) 
            for cloud_path 
            in self.list_files(dir_path)
        ]


    def get_url(self, cloud_path: str):
        location = self.s3.get_bucket_location(Bucket=self.bucket_name)['LocationConstraint']
        return f"https://{self.bucket_name}.s3.{location}.amazonaws.com/{cloud_path}"


    def create_presigned_url(self, cloud_path: str, expiration=3600):
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=cloud_path)
        except ClientError:
            return None
        
        url = self.s3.generate_presigned_url(
            ClientMethod='get_object', 
            Params={'Bucket': self.bucket_name, 'Key': cloud_path},
            ExpiresIn=expiration
        )

        return url


    def copy_object_to(
        self, 
        origin_cloud_path: str, 
        destination_bucket: str, 
        destination_cloud_path: str
    ):
        copy_source = {
            'Bucket': self.bucket_name,
            'Key': origin_cloud_path
        }
        return self.s3.copy(copy_source, destination_bucket, destination_cloud_path)
   
   
    def copy_dir_to(
        self, 
        origin_cloud_dir: str, 
        destination_bucket: str, 
        destination_cloud_dir: str
    ):
        return [
            self.copy_object_to(
                cloud_path, 
                destination_bucket, 
                cloud_path.replace(origin_cloud_dir, destination_cloud_dir)
            ) 
            for cloud_path in self.list_files(origin_cloud_dir)
        ]
