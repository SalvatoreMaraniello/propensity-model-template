"""
This module contain the main engines of the service. These are used to estimate likelihood of
conversion and potential booking value.
"""
import os
import pathlib
import datetime
import logging
import pandas as pd
import sklearn.preprocessing
import sklearn.pipeline
from sklearn.compose import ColumnTransformer
import sklearn.impute
import sklearn.calibration
from imblearn.ensemble import BalancedRandomForestClassifier

# local
import lib_yaml
import connector


queries_collection = lib_yaml.read_yaml_from_dir(
    os.path.join(pathlib.Path(__file__).parent.as_posix(), "collection")
)


class PropensityEngine():

    def __init__(self,
                 datetime_from: datetime.datetime,
                 datetime_to: datetime.datetime,
                 lookback_window_days: int,
                 conversion_window_days: int,
                 run_mode: str,
                 estimator=None,
                 estimator_params: dict = {},
                 calibration_params: dict = {}
                 ):
        """Train/predict propensity run_model. 

        Assign (potential) booking value to leads created in a datetime range. Lead value is 
        inferred from search history in a lookback window.

        Args:
            datetime_from (datetime): start of dates range.
            datetime_to (datetime): end of dates range.
            lookback_window_days (int): number of days defining lookback window to extract user session data.
            conversion_window_days (int): time window (in days) after leads generated where we look for lead conversion. Neglected when `run_mode = 'predict'`.
            run_mode (str): defines whether the model runs in `predict` or `train` mode.
            estimator: for `run_mode="predict"`. Defaults to None.
            estimator_params (dict, optional): _description_. Defaults to {}.
            caliobration_params (dict, optional): Parameters for probabilities calibration. Defaults to {}.


        Raises:
            ValueError: for incorrect `run_mode` value.
        """

        self.datetime_from = datetime_from
        self.datetime_to = datetime_to
        self.lookback_window_days = lookback_window_days

        # some checks
        _run_mode_values = ('train', 'predict', 'test')
        if run_mode not in _run_mode_values:
            raise ValueError(f"`run_mode` must be in {_run_mode_values}.")
        self._run_mode = run_mode

        # Model features.
        # Features are here grouped by category, which will determine pre-processing steps in a
        # scikit-learn pipeline.
        # In real-life, even if features belong to the same category we may want to build different
        # pipelines. For e.g., for different numerical features one may choose different
        # imputing/scaling methods.
        self._features_numerical = ['num-feat-2', 'list of numerical features']
        self._features_categorical = [
            'cat-feat-1', 'cat-feat-2', 'list of categorical features']
        self._features_all = self._features_numerical + self._features_categorical

        if self._run_mode == 'train' and not estimator_params:
            logging.warning(f'Found no parameters for estimator.')
        self.estimator_params = estimator_params
        self.calibration_params = calibration_params
        self.estimator = None

        logging.info(f'Propensity model initialised in `{run_mode}` mode.')

    def run(self):
        """Run pipeline. This method will load input data, preprocess them and either train/generate
        predictions.
        """

        self.load_leads_data()
        self.build_dataframes()

        if self._run_mode == 'train':

            # # load target data to self.df_target
            # This dataframe should countan lead conversion outcome, as well as userId and
            # leadCreateEventId - so as to allow sorting records to match sorting in self.df_input
            self.df_target = pd.DataFrame(
                data=[], columns=['userId', 'leadCreateEventId', 'converted'])
            logging.info("Loaded target for training.")

            # build/fit estimator pipeline.
            self.build_pipeline()
            # self.estimator.fit(
            #     self.df_input, self.df_target['converted'].values.reshape(-1)
            # )
            self.check_estimator()
            logging.info("Propensity model trained.")

        else:
            # probs = self.estimator.predict_proba( self.df_input)[:,1]
            # self.df_output['conversion_probability'] = probs
            logging.info("Propensity model run successfully.")

    def load_leads_data(self):
        """Load data about leads. These are read as pandas DataFrames and attached as attributes to 
        self."""

        # connect to database
        # conn = connector.PostgreSqlConnector()

        # self.df_events_count = conn.read_sql_query(
        #         queries_collection["leads_median_value"]["query"],
        #         params = {
        #             k: getattr( self, k) for k in queries_collection["leads_median_value"]["params"]
        #         }
        #     )
        logging.info("Loaded engagement data.")

        # load other useful suer data, e.g. device, location, demographic, etc.
        logging.info("Loaded user info.")

    def build_dataframes(self):
        """Build input dataframe for propensity model. This step generally includes:

        - data type conversion
        - joining sources from different input tables.
        - deduplication
        - engineering new features

        *Important*:
        DO NOT add here preprocessing steps that depend on data values. For e.g., imputing 
        missing values, scaling, replacing uncommon categories should not be done here!
        """

        # check all input tables have been loaded
        pass

        # check all inputs include the same leads
        pass

        # # Build input dataframe.
        # - This contains all the festures required by the propensity model.
        # - This step will generally including joining data from different sources on userId and leadCreateEventId.

        # # check we got all (and only) expected columns
        # if set( self.df_input) != set( self._features_all):
        #   raise ValeError("Unexpected/missing features in input dataframe")

        # demo/empty dataframe
        self.df_input = pd.DataFrame(data=[], columns=self._features_all)

        # store users/leads ids
        if self._run_mode == 'predict':
            self.df_output = pd.DataFrame(
                data=[], columns=['userId', 'leadCreateEventId', 'model-id', 'version', 'other-info'])

    def build_pipeline(self):
        """Build a scikit-learn pipeline for processing model features and train model. In this demo
        model we assume all numerical and categorical features are processed in the same way. More
        generally, however, one would perform different steps for different features.
        """

        # define demo pipeline.
        num_features_pipeline = sklearn.pipeline.Pipeline([
            # step 1. replace missing vals with median
            ('imputer', sklearn.impute.SimpleImputer(strategy='median')),
            # step 2. apply standard scaler
            ('scaler', sklearn.preprocessing.StandardScaler()),
            # add more steps here if needed
        ])
        cat_features_pipelines = sklearn.pipeline.Pipeline([
            # step 1. apply 1-hot encoding.
            # Ignore unseen categories and replace infrequent categories
            ('one-hot-enc', sklearn.preprocessing.OneHotEncoder(
                handle_unknown='ignore', min_frequency=0.05)),
            # add more steps here if needed
        ])

        preproc_pipeline = ColumnTransformer([
            ('numerical features', num_features_pipeline, self._features_numerical),
            ('categorical features', cat_features_pipelines,
             self._features_categorical),
            # add more transformer here
        ])

        forecast_pipeline = sklearn.pipeline.Pipeline([
            ('preprocess', preproc_pipeline),
            ('estimate', BalancedRandomForestClassifier(self.estimator_params))
        ])

        if self.calibration_params:
            self.estimator = sklearn.calibration.CalibratedClassifierCV(
                forecast_pipeline, **self.calibration_params
            )
        else:
            self.estimator = forecast_pipeline

        logging.info('Estimator pipeline built successfully.')

    def check_estimator(self):
        """Quality checks to ensure the retrained model has expected performance. Raise error 
        if model does not meet standards.
        """
        pass


class ValueEngine():

    def __init__(self, datetime_from: datetime.datetime, datetime_to: datetime.datetime, lookback_window_days: int):
        """Assign (potential) booking value to leads created in a datetime range. Lead value is 
        inferred from search history in a lookback window.

        Args:
            datetime_from (datetime): start of dates range.
            datetime_to (datetime): end of dates range.
            lookback_window_days (int): number of days defining lookback window.
        """

        self.datetime_from = datetime_from
        self.datetime_to = datetime_to
        self.lookback_window_days = lookback_window_days

    def predict(self, method: str = 'med', correct_available: bool = True):
        """Predict leads value.

        Args:
            method (str, optional): defines the method used to infer booking value. Defaults to 
            'med'. Strategies available:
                - 'avg': assigns booking value as weighted average of all searches.
                - 'med': assigns booking value as median of all searches.
                - We could add here more strategies.
            correct_available (bool, optional): If lead has converted, use exact booking value based 
            on transaction record. Defaults to True.
        """

        # connect to database
        # conn = connector.PostgreSqlConnector()

        # for simple startegies, e.g. avg, load (aggregate) booking value directly.
        if method == 'med':
            # self.df_output = conn.read_sql_query(
            #     queries_collection["leads_median_value"]["query"],
            #     params = {
            #         k: getattr( self, k) for k in queries_collection["leads_median_value"]["params"]
            #     }
            # )
            self.df_output = pd.DataFrame(
                data=[], columns=['userId', 'leadCreateEventId', 'booking_value'])
            logging.info("Computed leads potential booking value.")

        # for more complex strategies, we may need to load all searches.
        pass

        if correct_available:
            pass
            # load recent transactions and replace available booking values.
            logging.info(
                "Leads potential booking value corrected based on available transactions.")
