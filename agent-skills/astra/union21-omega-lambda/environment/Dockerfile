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
        astra-tools==0.2.17 \
        matplotlib==3.10.3 \
        numpy==2.2.6 \
        pytest==8.4.1 \
        pyyaml==6.0.2 \
        scipy==1.16.0 \
        uv==0.11.11 \
        "git+https://github.com/LightconeResearch/lightcone-cli.git@${LIGHTCONE_COMMIT}"

# The harness runs the agent as an unprivileged user with HOME=/home/<user>
# and the verifier as root, so nothing the agent needs may live only in /root.
#
# The astra skill uses this exact uvx command. Populate one shared uv cache
# while the image can reach the package index and leave it writable, because
# uvx builds its ephemeral environment inside the cache and a read-only copy
# fails for a non-root user. Do not force uv offline here: the harness installs
# its own model proxy in the sandbox with uv, and the agent's egress is already
# rejected by the harness firewall. The verifier never reads this cache: it
# validates through the root-owned pip-installed `astra`.
ENV UV_CACHE_DIR=/opt/uv-cache
RUN uvx astra-tools@0.2.17 --help >/dev/null \
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

# Pre-cache the Suzuki et al. 2012 paper (arXiv 1105.3470) into astra-tools'
# paper cache so quote verification does not depend on arXiv being reachable
# at run time. astra-tools reads $HOME/.cache/astra/{papers,text_cache}; seed
# it for root, then mirror into /etc/skel so the agent user (whose HOME the
# harness creates from /etc/skel) gets the same cache without a download.
RUN uvx astra-tools@0.2.17 paper add "10.48550/arXiv.1105.3470" \
    && uvx astra-tools@0.2.17 paper verify-quote "10.48550/arXiv.1105.3470" \
        --quote "In a flat Universe, SNe Ia alone constrain the dark-energy density, ΩΛ, to be ΩΛ = 0.705+0.040−0.043 including systematics" \
        --page 17 \
    && cp -a /root/.cache/astra /etc/skel/.cache-astra-seed \
    && mkdir -p /etc/skel/.cache \
    && cp -a /etc/skel/.cache-astra-seed /etc/skel/.cache/astra \
    && rm -rf /etc/skel/.cache-astra-seed \
    && chmod -R a+rX /root/.cache/astra /etc/skel/.cache

# Never bake skills into the image — skills are a run-time axis of the benchmark.

COPY project /root/sn-cosmology
WORKDIR /root/sn-cosmology

# The harness chowns the workspace to the agent user, but /root itself is
# 0700 on this base image, which leaves /root/sn-cosmology unreachable to
# that user.
RUN chmod 711 /root
