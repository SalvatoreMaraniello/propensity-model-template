"""
This module contain a class to connect and query from a PostgreSQL database. It uses sqlalchemy 
engine [1] with a Psycopg driver [2,3].

Notes:
    * For compatibility we use psycopg2-binary, which is a pre-compiled version of Psycopg [2].
    * Psycopg can be used also without sqlalchemy. However, sqlalchemy allows nice formatting
        when used with pandas - e.g. retrieve column names automatically.
    * Other drivers are available (and may be faster). Sqlalchemi supports the following [3].

References:
    1. https://docs.sqlalchemy.org/en/14/core/engines.html
    2. https://www.psycopg.org/docs/install.html#install-from-source
    3. https://docs.sqlalchemy.org/en/14/dialects/postgresql.html
    4. https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2
"""

import os
import urllib
from typing import Optional, Union
import sqlalchemy

from sqlalchemy.engine import Connection
from sqlalchemy import create_engine
import pandas as pd


class PostgreSqlConnector:
    """
    PostgreSQL connector.

    Args:
        user (str, optional): POSTGRES database username. If `None`, this is set as per `POSTGRES_USER`
            env variable.
        password (str, optional): POSTGRES database password. If `None`, this is set as per
            `POSTGRES_PASSWORD` env variable.
        database (str): Database name. If `None`, this is set as per `POSTGRES_DATABASE` env variable.
        host (str, optional): Database URL/IP address. If `None`, this is set as per `POSTGRES_URI` env
            variable.
        port (str, optional): Database port. If `None`, this is set as per `POSTGRES_PORT` env variable.

        References:
            1. https://docs.sqlalchemy.org/en/14/core/engines.html
            2. https://www.psycopg.org/docs/install.html#install-from-source
            3. https://docs.sqlalchemy.org/en/14/dialects/postgresql.html
            4. https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2
    """

    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[str] = None,
    ):

        # set defaults
        if user is None:
            if 'POSTGRES_USER' not in os.environ:
                raise ValueError(
                    "POSTGRES_USER environmental variable not found.")
            user = os.environ['POSTGRES_USER']
        if password is None:
            if 'POSTGRES_PASSWORD' not in os.environ:
                raise ValueError(
                    "POSTGRES_PASSWORD environmental variable not found.")
            password = os.environ['POSTGRES_PASSWORD']
        if database is None and 'POSTGRES_DATABASE' in os.environ:
            database = os.environ['POSTGRES_DATABASE']
        if host is None:
            if 'POSTGRES_HOST' not in os.environ:
                raise ValueError(
                    "POSTGRES_HOST environmental variable not found.")
            host = os.environ['POSTGRES_HOST']
        if port is None:
            port = os.environ['POSTGRES_PORT'] if 'POSTGRES_PORT' in os.environ else 5432
        self.engine = create_engine(
            f'postgresql+psycopg2://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{database}'
        )

    def get_connection(self) -> Connection:
        """
        Returns a connection object [7].

        Examples:
            Connection objects can be used in `with` statements
            >>> conn = PostgreSqlConnector()
            >>> with conn.get_connection() as c_active:
            >>>     res = c_active.execute('select * from TABLE limit 3')
        """
        return self.engine.connect()

    def execute(self, sql_query: Union[str, sqlalchemy.text], params: dict = None) -> sqlalchemy.engine.cursor.CursorResult:
        """
        Execute SQL query and returns a `CursorResult` SQL object. Data can be fetched using the
        `fetch*` methods attached to the cursor.

        Args:
            sql_query: query to run. For queries using parameters, the function employs
            `sqlalchemy.text` and parameters should be indicated as `:param-name` [8].
            params (dict, optional): dictionary specifying the query parameters values.

        Returns:
            param1 (sqlalchemy.engine.cursor.CursorResult): results cursor with attached methods to
                fetch the data.

        Examples:

            Here is a sample query with two parameters:

            >>> conn = PostgreSqlConnector( database = 'xxx')
            >>> res = conn.execute(
            ...    'select * from table-name where id>:minId limit :rows',
            ...    params = {'minId': 1000, 'rows': 4} )
            ... data = res.fetchall()
        """
        if params is None:
            params = {}
        with self.engine.connect() as con:
            # use con.execution_options().execute if needed
            res = con.execute(sqlalchemy.text(sql_query), params)
        return res

    def read_sql_query(
            self, sql_query: Union[str, sqlalchemy.text], **kwargs) -> pd.DataFrame:
        """
        Wrapper of `pandas.read_sql_query` to read SQL statements into DataFrames.

        Args:
            sql_query: query to run. For queries using parameters, the function employs
            `sqlalchemy.text` and parameters should be indicated as `:param-name` [8].
            kwargs: any optional argument of `pandas.read_sql_table`. Useful parameters are:
                params (dict): dictionary specifying the query parameters values.

        Returns:
            param1 (pandas.DataFrame): output table as a pandas DataFrame object.

        Examples:

            Here is a sample query with two parameters:

            >>> conn = PostgreSqlConnector( database = 'xxx')
            >>> df = conn.read_sql_query(
            ...    'select * from table-name where id>:minId limit :rows',
            ...    params = {'minId': 1000, 'rows': 4} )
        """

        if isinstance(sql_query, str) and ('params' in kwargs):
            sql_query = sqlalchemy.text(sql_query)

        return pd.read_sql_query(sql_query, self.get_connection(), **kwargs)
