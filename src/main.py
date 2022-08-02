"""Run propensity model.
"""

import os
import logging
from datetime import datetime, date, timedelta

# local
import lib_yaml
import lib_io
import engines
import connector

# some settings


def main(run_mode: str, params: dict, exec_time: str = None):
    """Run propensity model in either train or predict mode.

    Args:
        run_mode (str): Must be equal to "train" or "predict". In the first case, the propensity model 
            s retrained and updated in GCP. In the second case, the leads coversion likelihood and potential 
            value is forecast. Output is stored in data warehouse.
        params (dict): Model parameters. Refer to `src/params.yaml` for more details.
        exec_time (str, optional): String in format "%Y-%m-%d" defining the date when the model is 
            executed. Note that time is different than run time. For e.g.g, if `exec_time='2022-06-30'`, 
            the model will load data about leads crearted up until "2022-06-30 00:00:00". Defaults to current date.
    """

    # some checks here...
    _run_mode_values = ('train', 'predict', 'test')
    if run_mode not in _run_mode_values:
        raise ValueError(f"`run_mode` must be in {_run_mode_values}.")

    # extract correct set of params
    params = (params['general'] | params['run_mode'][run_mode])

    # define date range
    if not exec_time:
        datetime_to = datetime.combine(date.today(), datetime.min.time())
    else:
        datetime_to = datetime.strptime(exec_time, '%Y-%m-%d')
    datetime_from = datetime_to - \
        timedelta(days=params['dates_process_range_days'])
    logging.info(
        f'Processing leads in dates range: {datetime_from} -> {datetime_to}.')

    # # check if some leads have already been processed.
    # - depending on our infra, we may choose to allow for some overlap.
    # - if some leads in [datetime_from, datetime_to] have already been processed, adjust range.

    # load estimator for booking probability
    estimator = (
        None if run_mode == 'train'
        # lib_io.load_estimator( params['model-id'], os.environ['BUCKET_NAME'])
        else None
    )

    # run prediction/training
    prop_eng = engines.PropensityEngine(
        datetime_from, datetime_to,
        params['lookback_window_days'],
        params['conversion_window_days'],
        run_mode,
        estimator,
        params.get('estimator_params'),
        params.get('calibration_params')
    )
    prop_eng.run()

    # dump model
    if run_mode == 'train':
        # lib_io.save_estimator()
        logging.info('Propensity model estimator updated in GCP.')
        return

    # predict (potential) booking value
    value_eng = engines.ValueEngine(
        datetime_from, datetime_to, params['lookback_window_days']
    )
    value_eng.predict()

    # save to data warehouse
    df_output = prop_eng.df_output.merge(
        value_eng.df_output, on=['userId', 'leadCreateEventId'], how='left'
    )
    # conn = connector.PostgreSqlConnector()
    # df_output.to_sql(
    #     'destination-table-name', conn.get_connection(),
    #     schema='sink', if_exists='append', index=False,
    #     chunksize=None)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)

    main(
        run_mode=os.environ['RUN_MODE'],
        params=lib_yaml.read_yaml('./params.yaml'),
        exec_time=os.environ.get('EXEC_TIME', None)
    )
