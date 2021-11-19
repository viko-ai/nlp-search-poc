FROM python:3.9.7-alpine3.14

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src
COPY ./conf /code/conf
COPY ./data /code/data

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "conf/logging.conf"]