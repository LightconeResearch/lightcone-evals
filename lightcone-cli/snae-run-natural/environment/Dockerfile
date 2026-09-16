FROM python:3.12-slim

# CI's materialize.sh rewrites this line to pin the stack under test
# (stack_ref). Keep the exact "ARG LIGHTCONE_COMMIT=" spelling.
ARG LIGHTCONE_COMMIT=main

# lc scrubs ambient UV_* settings from recipe environments, except these two
# (see lightcone/engine/project.py): a shared managed interpreter and a
# shared package cache, seen identically by root (oracle, verifier) and the
# unprivileged agent user.
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    UV_CACHE_DIR=/opt/uv-cache

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        jq \
        procps \
        ripgrep \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir uv==0.12.13 pytest==8.4.1 pyyaml==6.0.2 \
    && uv python install 3.12

# lc (whose entry points mirror the git-annex executables, so `git add` of
# annexed files works) and astra, installed the way a user installs them —
# `uv tool install` — but linked system-wide so every user sees the same
# tools. astra is pinned to the version this lightcone-cli depends on.
RUN UV_TOOL_DIR=/opt/uv-tools UV_TOOL_BIN_DIR=/usr/local/bin \
    uv tool install --python 3.12 \
        "git+https://github.com/LightconeResearch/lightcone-cli.git@${LIGHTCONE_COMMIT}" \
    && UV_TOOL_DIR=/opt/uv-tools UV_TOOL_BIN_DIR=/usr/local/bin \
    uv tool install --python 3.12 \
        "astra-tools==$(/opt/uv-tools/lightcone-cli/bin/python -c 'import importlib.metadata as m; print(m.version("astra-tools"))')"

# The image prepares realistic starting states, not an agent tutorial.
RUN git config --system user.name "Lightcone Eval" \
    && git config --system user.email eval@lightcone \
    && git config --system init.defaultBranch main \
    && git config --system --add safe.directory '*'

COPY seed/ /opt/snae-natural-reference/seed/
COPY prepare.py /tmp/prepare-snae.py
RUN python3 /tmp/prepare-snae.py \
    && rm /tmp/prepare-snae.py \
    && chmod -R go-rwx /opt/snae-natural-reference

RUN useradd -m -s /bin/bash agent \
    && chown -R agent:agent /root/snae-natural \
    && chmod -R a+rX /opt/uv-tools /opt/uv-python \
    && chmod -R a+rwX /opt/uv-cache /root/snae-natural \
    && chmod 711 /root
WORKDIR /root/snae-natural
