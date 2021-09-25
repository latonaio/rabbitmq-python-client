FROM python:3.9.6-slim-buster

# Definition of a Device & Service
ENV POSITION=Runtime \
    SERVICE=message-relayer-python \
    AION_HOME=/var/lib/aion

RUN mkdir ${AION_HOME}
WORKDIR ${AION_HOME}
# Setup Directoties
RUN mkdir -p \
    $POSITION/$SERVICE
WORKDIR ${AION_HOME}/$POSITION/$SERVICE/

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    git \
    openssh-client \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /root/.ssh/ && touch /root/.ssh/known_hosts && ssh-keyscan -t rsa bitbucket.org >> /root/.ssh/known_hosts

COPY . .
# COPY requirements.txt .
RUN --mount=type=secret,id=ssh,target=/root/.ssh/id_rsa pip3 install -r requirements.txt

CMD ["python3", "-u", "main.py"]
