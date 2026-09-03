FROM python:3.13-slim

ARG LIGHTCONE_COMMIT=229bcc5d282634e09e251ec5195115251b1cbb63

ENV DEBIAN_FRONTEND=noninteractive \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        procps \
        ripgrep \
        time \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
        astra-tools==0.2.13 \
        jsonschema==4.24.0 \
        matplotlib==3.10.3 \
        numpy==2.2.6 \
        pytest==8.4.1 \
        scipy==1.16.0 \
        uv==0.11.11 \
        "git+https://github.com/LightconeResearch/lightcone-cli.git@${LIGHTCONE_COMMIT}"

# The harness runs the agent as an unprivileged user with HOME=/home/<user>
# and the verifier as root, so nothing the agent needs may live only in /root.
#
# The async skill uses this exact uvx command. Populate one shared uv cache
# while the image can reach the package index and leave it writable, because
# uvx builds its ephemeral environment inside the cache and a read-only copy
# fails for a non-root user. Do not force uv offline here: the harness installs
# its own model proxy in the sandbox with uv, and the agent's egress is already
# rejected by the harness firewall. The verifier never reads this cache: it
# validates through the root-owned pip-installed `astra`.
ENV UV_CACHE_DIR=/opt/uv-cache
RUN uvx astra-tools@0.2.13 --help >/dev/null \
    && chmod -R a+rwX /opt/uv-cache

# lc reads ~/.lightcone/config.yaml. Seed it for root (oracle and verifier)
# and, through /etc/skel, for any user the harness creates at run time.
RUN mkdir -p /etc/skel/.lightcone \
    && printf '%s\n' \
        'container:' \
        '  runtime: none' \
        'slurm:' \
        '  account: null' \
        '  time_padding: 1.5' \
        > /etc/skel/.lightcone/config.yaml \
    && cp -a /etc/skel/.lightcone /root/.lightcone

COPY project /root/snae
WORKDIR /root/snae

# The harness chowns the workspace to the agent user, but /root itself is
# 0700 on this base image, which leaves /root/snae unreachable to that user.
RUN chmod 711 /root
