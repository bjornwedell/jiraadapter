FROM python:3.7-slim as base

RUN pip3 install --upgrade pip
RUN pip3 install jira==2.0.0
RUN pip3 install aiohttp==3.5.4
RUN pip3 install watchdog==0.9.0

FROM base AS test
COPY . test
ENV PYTHONPATH "/test/"
CMD python3 -m unittest /test/test/*.py

FROM base
COPY app app
CMD watchmedo auto-restart -d=/app -R --pattern=*.py -- python3 -m app
