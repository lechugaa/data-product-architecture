import luigi
import luigi.contrib.s3

from src.pipeline.ingesta_almacenamiento import get_s3_resource
from src.pipeline.limpieza_feature_eng import DataEngineer
from src.orchestration.clean_data_metadata_task import CleanDataMetaTask
from src.utils.general import get_file_path, get_upload_path, get_s3_credentials
from src.utils.constants import bucket_name


class FeatureEngineeringTask(luigi.Task):

    # class attributes
    historic = luigi.BoolParameter(default=False)
    query_date = luigi.DateParameter(default=None)

    def requires(self):
        return CleanDataMetaTask(historic=self.historic, query_date=self.query_date)

    def run(self):

        # obtaining paths
        file_path = get_file_path(historic=self.historic, query_date=self.query_date, prefix=DataEngineer.prefix)
        upload_path = get_upload_path(historic=self.historic, query_date=self.query_date, prefix=DataEngineer.prefix)

        # execute process
        fe = DataEngineer(self.historic, self.query_date)
        fe.generate_features(save=True)

        # uploading file
        s3_resource = get_s3_resource()
        s3_resource.meta.client.upload_file(file_path, bucket_name, upload_path)

    def output(self):
        s3_credentials = get_s3_credentials("conf/local/credentials.yaml")
        client = luigi.contrib.s3.S3Client(
            aws_access_key_id=s3_credentials['aws_access_key_id'],
            aws_secret_access_key=s3_credentials['aws_secret_access_key']
        )

        upload_path = get_upload_path(historic=self.historic, query_date=self.query_date, prefix=DataEngineer.prefix)
        output_path = f"s3://{bucket_name}/{upload_path}"

        return luigi.contrib.s3.S3Target(path=output_path, client=client)
