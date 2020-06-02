FROM python:3.7-slim

RUN pip3 install --upgrade pip
RUN pip3 install jira==2.0.0
RUN pip3 install aiohttp==3.5.4
RUN pip3 install watchdog==0.9.0

COPY app app

CMD watchmedo auto-restart -d=/app -R --pattern=*.py -- python3 -m app