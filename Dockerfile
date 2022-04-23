FROM python:3.9-slim

# app user
ENV USER app
ENV UID 1001
RUN useradd -ms /bin/bash --uid=${UID} ${USER}

# setup app directory
COPY src/* /${USER}/
RUN chown ${USER}:${USER} /${USER}

# get required dependencies
COPY requirements.txt /${USER}/
RUN pip3 install -r /${USER}/requirements.txt

# run as non-root user
USER ${USER}
WORKDIR /${USER}
ENTRYPOINT [ "python3", "main.py" ]
