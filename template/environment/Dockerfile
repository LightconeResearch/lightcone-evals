FROM python:3.13-slim

# CI's materialize.sh rewrites this line to pin the stack under test
# (stack_ref). Keep the exact "ARG LIGHTCONE_COMMIT=" spelling.
ARG LIGHTCONE_COMMIT=main

ENV DEBIAN_FRONTEND=noninteractive \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        procps \
        time \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
        pytest==8.4.1 \
        "git+https://github.com/LightconeResearch/lightcone-cli.git@${LIGHTCONE_COMMIT}"

# The harness runs the agent as an unprivileged user with HOME=/home/<user>
# and the verifier as root, so nothing the agent needs may live only in /root,
# and anything pre-baked must be world-readable (a+rX — see the snae task's
# Dockerfile for the uv-cache and /etc/skel config patterns).

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

# Never bake skills into the image — skills are a run-time axis of the benchmark.

COPY project /root/project
WORKDIR /root/project

# The harness chowns the workspace to the agent user, but /root itself is
# 0700 on this base image, which leaves the workspace unreachable to that user.
RUN chmod 711 /root
