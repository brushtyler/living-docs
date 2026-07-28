FROM python:3.12-slim-bookworm

ARG CHROME_VERSION=138.0.7204.168

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        xdg-utils \
    && curl -fsSLo /tmp/chrome.zip \
        "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" \
    && curl -fsSLo /tmp/driver.zip \
        "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip -q /tmp/chrome.zip -d /opt \
    && unzip -q /tmp/driver.zip -d /opt \
    && ln -s /opt/chrome-linux64/chrome /usr/local/bin/google-chrome \
    && ln -s /opt/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm -f /tmp/chrome.zip /tmp/driver.zip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY . .
RUN python -m pip install --no-cache-dir .

WORKDIR /workspace
ENV SE_OFFLINE=true
ENTRYPOINT ["living-docs-mcp"]
CMD ["--project-root", "/workspace"]
