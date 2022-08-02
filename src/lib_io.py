"""
Library with input/output utils.
"""

import os
import datetime
from google.cloud import storage
import joblib
import json
import logging


def load_estimator(file_name_root: str, bucket_name: str):
    """Load estimator and setting files from GCP bucket.

    Args:
        file_name_root (str): model identifier.
        file_name_root (str): model name.

    Returns:
        estimator: _description_
    """

    # copy locally from storage
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    logging.info('Bucket object created')

    # read estimator
    blob_name_estimator = 'models/%s_default.joblib' % file_name_root
    logging.info('Loading %s' % blob_name_estimator)
    blob = bucket.get_blob(blob_name_estimator)
    blob.download_to_filename('./estim_default.joblib')

    # # read settings
    # blob_name_settings = 'models/settings_%s_default.json' %file_name_root
    # logging.info('Loading %s' %blob_name_settings)
    # blob = bucket.get_blob( blob_name_settings )
    # blob.download_to_filename( './settings_default.json' )

    logging.info('Estimator loaded successfully from %s' % bucket_name)

    # load objects
    estimator = joblib.load('./estim_default.joblib')
    # with open( './settings_default.json', 'r') as fp:
    #     params = json.load(fp)

    return estimator  # , params


def save_estimator(estimator, params, file_name_root: str, bucket_name=None):
    '''
    Dumps estimator to bucket together with parameters required to run in json
    '''

    if not bucket_name:
        bucket_name = os.environ['BUCKET_NAME']

    # connect to storage
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    # ----- save estimator
    # dump local
    joblib.dump(estimator, './estim_default.joblib')
    # upload as default
    blob = bucket.blob('models/%s_default.joblib' % file_name_root)
    blob.upload_from_filename('./estim_default.joblib')
    # upload to models history
    blob = bucket.blob(
        'models/versions/%s_%s.joblib' % (
            file_name_root,
            str(datetime.date.today()),
        )
    )
    blob.upload_from_filename('./estim_default.joblib')

    # # save settings file
    # # dump local
    # with open( './settings_default.json', 'w') as fp:
    #     json.dump(params, fp)

    # # upload as default
    # blob = bucket.blob('models/settings_%s_default.json' %file_name_root)
    # blob.upload_from_filename( './settings_default.json' )

    # # upload to history
    # blob = bucket.blob(
    #     'models/versions/settings_%s_%s.json' %(
    #         file_name_root,
    #         str(datetime.date.today()),
    #     )
    # )
    # blob.upload_from_filename( './settings_default.json' )
