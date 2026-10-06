FROM python:3.12-slim

# CI's materialize.sh rewrites this line to pin the stack under test
# (stack_ref). Keep the exact "ARG LIGHTCONE_COMMIT=" spelling.
ARG LIGHTCONE_COMMIT=b79d2a329b86805656689464604735c433f73267

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

RUN python -m pip install --no-cache-dir uv==0.12.13 \
    && uv python install 3.12

# lc and astra, installed the way a user installs them — `uv tool install` —
# but linked system-wide so every user sees the same tools. astra is pinned
# to the version this lightcone-cli depends on; the verifier imports astra
# from its tool environment (/opt/uv-tools/astra-tools/bin/python).
RUN UV_TOOL_DIR=/opt/uv-tools UV_TOOL_BIN_DIR=/usr/local/bin \
    uv tool install --python 3.12 \
        "git+https://github.com/LightconeResearch/lightcone-cli.git@${LIGHTCONE_COMMIT}" \
    && UV_TOOL_DIR=/opt/uv-tools UV_TOOL_BIN_DIR=/usr/local/bin \
    uv tool install --python 3.12 \
        "astra-tools==$(/opt/uv-tools/lightcone-cli/bin/python -c 'import importlib.metadata as m; print(m.version("astra-tools"))')"

# The project the agent starts from: a plain directory, no git, no lc.
COPY project /root/line-fit

# The harness runs the agent as an unprivileged user with HOME=/home/<user>
# and the verifier as root: tools and interpreter readable by all, the
# project writable, and /root traversable (it is 0700 on this base image).
RUN chmod -R a+rX /opt/uv-tools /opt/uv-python \
    && chmod -R a+rwX /opt/uv-cache /root/line-fit \
    && chmod 711 /root

WORKDIR /root/line-fit
