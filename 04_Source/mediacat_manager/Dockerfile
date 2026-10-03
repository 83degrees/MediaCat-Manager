FROM ghcr.io/home-assistant/base-python:3.14-alpine3.24

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

COPY run.sh /run.sh
COPY requirements.txt /requirements.txt
COPY app /app

RUN pip3 install --no-cache-dir -r /requirements.txt \
    && chmod a+x /run.sh

CMD ["/run.sh"]
