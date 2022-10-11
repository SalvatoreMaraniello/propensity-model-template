# import engines 

import sklearn.impute 
import sklearn.preprocessing
import sklearn.pipeline 
from sklearn.compose import ColumnTransformer
from imblearn.ensemble import BalancedRandomForestClassifier
import sklearn.ensemble
import sklearn.calibration

import pandas as pd 

import sklearn.datasets

_fun_load_dataset = sklearn.datasets.load_diabetes

df = pd.DataFrame(
    data = _fun_load_dataset()['data'],
    columns = _fun_load_dataset()['feature_names']
)
y_target = pd.DataFrame( 
    data = _fun_load_dataset()['target'],
    columns = ['outcome']
)
# make it a (1,0) to resemble a classification problem
y_target = (y_target>120.0).astype(int)

# build dummy categorical features
df['sex'] = df['sex'].apply( lambda x: 'M' if (x<0) else'F')
df['cat_2'] = df['bp'].apply( lambda x: 'cat1' if (x<0) else ('cat2' if (x>0.1) else 'cat3'))

num_features_pipeline = sklearn.pipeline.Pipeline([
    ( 'imputer', sklearn.impute.SimpleImputer( strategy='median') ),
    ( 'scaler', sklearn.preprocessing.StandardScaler() ),
    # add more steps here if needed
])
cat_features_pipelines = sklearn.pipeline.Pipeline([
    ( 'one-hot-enc', sklearn.preprocessing.OneHotEncoder( handle_unknown='infrequent_if_exist', min_frequency=0.05) ),
    # add more steps here if needed
])

features_categorical = ['sex', 'cat_2']
features_numerical = [ 'age', 'bmi', 'bp' ]
    # col for col in df.columns if (col not in features_categorical)

preproc_pipeline = ColumnTransformer([
    ('numerical features', num_features_pipeline, features_numerical),
    ('categorical features', cat_features_pipelines, features_categorical)
])

forecast_pipeline = sklearn.pipeline.Pipeline([
    ( 'preprocess', preproc_pipeline),
    # ( 'estimate', BalancedRandomForestClassifier( n_estimators=20) )
    ( 'estimate', sklearn.ensemble.RandomForestClassifier( n_estimators=200) )
])

# add calibration
calibrated_forecast_pipeline = sklearn.calibration.CalibratedClassifierCV(
    forecast_pipeline, cv=2, method='isotonic'
    )

df_input = df[features_numerical + features_categorical]
forecast_pipeline.fit(df_input, y_target.values.reshape(-1) )

y_no_cal = forecast_pipeline.predict_proba( df_input)

calibrated_forecast_pipeline.fit(df_input, y_target.values.reshape(-1) )
y_cal = calibrated_forecast_pipeline.predict_proba( df_input)

dplot = pd.DataFrame(
    dict(
        no_calibration = y_no_cal[:,1], 
        calibration = y_cal[:,1]
    )
)








