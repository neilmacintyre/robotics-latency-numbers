FROM debian:bookworm-slim

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        capnproto \
        cmake \
        fastddsgen \
        flatbuffers-compiler \
        libbenchmark-dev \
        libcapnp-dev \
        libfastcdr-dev \
        libflatbuffers-dev \
        libfastrtps-dev \
        libprotobuf-dev \
        ninja-build \
        pkg-config \
        protobuf-compiler \
        python3-dev \
        python3-flatbuffers \
        python3-pip \
        python3-protobuf \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv --system-site-packages /opt/benchmark-venv \
    && /opt/benchmark-venv/bin/pip install --no-cache-dir \
        pycapnp \
        pytest \
        pytest-benchmark \
        rosbags

COPY msg_archetypes /opt/serialization_benchmarks/schemas
COPY serialization_benchmarks/generate_bindings.sh /usr/local/bin/generate-bindings
COPY serialization_benchmarks/entrypoint.sh /usr/local/bin/serialization-benchmark-entrypoint

RUN chmod +x \
        /usr/local/bin/generate-bindings \
        /usr/local/bin/serialization-benchmark-entrypoint \
    && generate-bindings \
        /opt/serialization_benchmarks/schemas \
        /opt/serialization_benchmarks/generated

ENV SERIALIZATION_BENCHMARK_ROOT=/opt/serialization_benchmarks
ENV PATH=/opt/benchmark-venv/bin:${PATH}
ENV PYTHONPATH=/opt/serialization_benchmarks/generated/python:/opt/serialization_benchmarks/generated/python/protobuf:/opt/serialization_benchmarks/generated/python/flatbuffers:/opt/serialization_benchmarks/generated/python/ros

WORKDIR /work

ENTRYPOINT ["/usr/local/bin/serialization-benchmark-entrypoint"]
CMD ["bash"]
