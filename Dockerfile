FROM python:3.9 as base

# define a working directory and copy files in there
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt

# add code to working directory
COPY src/ /code/ 

# ENV GOOGLE_APPLICATION_CREDENTIALS=service_account.json
CMD ["python","main.py"]