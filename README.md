# Propensity model template project

_S. Maraniello, Jul-22_

This repository contains a demo code for a propensity model that predicts the booking likelihood and
potential value of leads generated on client X website. The service:

- loads data about all leads generated in a time window;

- if `run_mode="train"` the model will then:

  - train a propensity model.

  - save model in GCP bucket.

- if `run_mode="predict"` the service will:

  - predict the leads likelihood of conversion.

  - infer the potential booking value.

  - save results in a data warehouse.

The service is composed by two main engines (see `engine.py`):

- a propensity engine, that infers the users booking probability from user info and session data;

- a value engine, that predicts the potential booking value based on user search history.

Model key parameters are stores in `src/params.yaml`. These include:

- `lookback_window_days`: this determine the time window used to detect user activity on client website.

- `conversion_window_days`: this determines the window used when detecting whether the lead was converted or not.

## Setup

This service will require credentials for accessing the data warehouse and Google bucket. These are stored in the following environmental variables. For local run, you can store these into `./.env` and source them as `source ./.env`.

```sh
DB_USER_ACCOUNT=xxx            # user with read/write permission for data warehouse
DB_USER_PASSWORD=xxx           # user password
BUCKET_NAME=xxx                # Google bucket where model is stored/loaded from
GOOGLE_APPLICATION_CREDENTIALS # credentials for GCP bucket access
RUN_MODE=train|predict         # use train or predict
EXEC_TIME=2022-07-22           # the model will process leads up to midnight of the day before.
```

## Run locally

To run the code in a local environment locally:

1. Create environment:

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip3 install --upgrade pip3
   pip3 install -r requirements.txt
   ```

1. Source environmental variables `source .env`.

1. `python main.py`.

Alternatively, the code can run in Docker container as:

```sh
# build image
docker build . -t propensity_model_image  -f ./Dockerfile

# run
docker run -it \
   -e DB_USER_ACCOUNT=$DB_USER_ACCOUNT \
   -e DB_USER_PASSWORD=$DB_USER_PASSWORD \
   -e BUCKET_NAME=$BUCKET_NAME \
   -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
   -e RUN_MODE=train \
   -e EXEC_TIME=2022-07-10 \
   propensity_model_image
```

## Repository Content

- `docs`. Documentation folder. This is built using Sphinx. See _Documentation_ section for more info. Documentation can be found under `./build/html/index.html`.

- `infra`. This folder would contain all necessary settings/script for infrastructure and deployment.

- `src`. source code.

  - `main.py`. Main service.

  - `params.yaml`. Model parameters. Refer to comments in file.

  - `engine.py`. Contains `PropensityEngine` and `ValueEngine` classes, used to forecast users propensity and booking potential value, respectively.

  - `connector.py`. A class to connect to a Postgres database. It offers simple functionalities to execute commands or read tables/queries into pandas DataFrames.

  - `lib_yaml.py`. Utilities to manipulate `yaml` files.

  - `collecition`. Collection of parametrised SQL queries to fetch data from data warehouse. Queries are casted in `yaml` files. Refer to `desc` parameter in each file for info.

  - `lib_io.py`. A few input output utilities (e.g. read/dump to GCP).

## Documentation

Documentation is built using Sphinx. From `./docs` run `make html` to generate documentation. The main index is found under `./build/html/index.html`.
Note that Sphinx is added to the project requirements; for deployment this can be removed from `requirements.txt`.

## Continuous Integration / Deployment

Add here instructions for deployment.
