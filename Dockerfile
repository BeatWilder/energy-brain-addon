ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.8
FROM ${BUILD_FROM}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apk add --no-cache python3 py3-pip

WORKDIR /opt/energy-brain
COPY requirements.txt ./
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

COPY energy_brain ./energy_brain
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
