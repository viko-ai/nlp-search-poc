#!/bin/ksh

uvicorn --port 8000 --reload src.server:app --log-config conf/logging.conf