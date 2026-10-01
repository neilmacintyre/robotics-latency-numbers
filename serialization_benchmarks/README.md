# Serialization benchmark container

This image provides matching C++ and Python environments for benchmarking:

- ROS 2 CDR without ROS (Fast DDS-Gen/Fast CDR in C++, `rosbags` in Python)
- Protocol Buffers
- Cap'n Proto
- FlatBuffers
- native C structs (C++ headers)
- Google Benchmark and `pytest-benchmark`

Build the image from the repository root:

```sh
docker build \
  -f serialization_benchmarks/Dockerfile \
  -t robotics-serialization-benchmarks .
```

Open a shell with the repository mounted at `/work`:

```sh
docker run --rm -it \
  -v "$PWD:/work" \
  robotics-serialization-benchmarks
```

Generated files are under `/opt/serialization_benchmarks/generated`:

- `cpp/`: Protobuf, Cap'n Proto, FlatBuffers, Fast CDR, and C-struct code
- `python/`: Protobuf, FlatBuffers, and `ctypes` modules, Cap'n Proto schemas,
  and the standalone `robotics_benchmark_msgs` ROS typestore

The entrypoint activates the Python environment and configures `PYTHONPATH`.

Run the quick Python matrix and save machine-readable results:

```sh
docker run --rm \
  -v "$PWD:/work" \
  robotics-serialization-benchmarks \
  pytest /opt/serialization_benchmarks/benchmarks/python \
    --benchmark-only \
    --benchmark-json=/work/python-quick.json
```

The suite defaults to the quick profile. Select a smaller development slice or
the full core profile with:

```sh
# One archetype across all serializers.
pytest /opt/serialization_benchmarks/benchmarks/python \
  --serialization-archetypes=small_flat \
  --serialization-operations=serialize,deserialize

# Full core profile.
pytest /opt/serialization_benchmarks/benchmarks/python \
  --serialization-profile=core \
  --benchmark-json=/work/python-core.json
```

Available selectors are `--serialization-serializers`,
`--serialization-archetypes`, `--serialization-operations`, and
`--serialization-case-filter`. Deserialization benchmarks traverse every
nested value and materialize large byte arrays so lazy-view formats perform
equivalent work. FlatBuffers has no separate mutable message construction
phase, so it is omitted from `construct_serialize`.

Create the standalone Python ROS type store with:

```python
from robotics_benchmark_msgs import create_typestore

typestore = create_typestore()
```

The official ROS 2 generators are deliberately not installed:
`rosidl_generator_cpp` and `rosidl_generator_py` depend on ament and ROS
runtime/type-support packages. Fast DDS-Gen produces C++ code using the same
CDR wire representation, while `rosbags` independently parses `.msg` files and
implements ROS 1 and ROS 2 serialization in Python. This measures serializer
performance, not `rclcpp` or `rclpy` object/type-support overhead.

Protobuf and Cap'n Proto cannot express a fixed-size repeated field in their
schemas, so benchmark code must enforce the 36-element invariant of
`FixedNumericArray`. Pycapnp loads `.capnp` schemas at runtime because Cap'n
Proto does not provide a separate Python source generator.
