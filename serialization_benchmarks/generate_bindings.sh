#!/usr/bin/env bash

set -euo pipefail

schema_root=${1:?Usage: generate_bindings.sh SCHEMA_ROOT OUTPUT_ROOT}
output_root=${2:?Usage: generate_bindings.sh SCHEMA_ROOT OUTPUT_ROOT}

cpp_root="${output_root}/cpp"
python_root="${output_root}/python"

rm -rf "${output_root}"
mkdir -p \
  "${cpp_root}/protobuf" \
  "${cpp_root}/capnproto" \
  "${cpp_root}/flatbuffers" \
  "${cpp_root}/cstructs" \
  "${cpp_root}/ros2_cdr" \
  "${python_root}/protobuf" \
  "${python_root}/flatbuffers" \
  "${python_root}/capnproto" \
  "${python_root}/cstructs" \
  "${python_root}/ros/robotics_benchmark_msgs/_schemas"

mapfile -t protobuf_schemas < <(
  find "${schema_root}/protobuf" -maxdepth 1 -name '*.proto' -print | sort
)
protoc \
  --proto_path="${schema_root}/protobuf" \
  --cpp_out="${cpp_root}/protobuf" \
  --python_out="${python_root}/protobuf" \
  "${protobuf_schemas[@]}"
touch "${python_root}/protobuf/__init__.py"

mapfile -t capnproto_schemas < <(
  find "${schema_root}/capnproto" -maxdepth 1 -name '*.capnp' -print | sort
)
capnp compile \
  --src-prefix="${schema_root}/capnproto" \
  -oc++:"${cpp_root}/capnproto" \
  "${capnproto_schemas[@]}"
cp "${schema_root}/capnproto/"*.capnp "${python_root}/capnproto/"
cat > "${python_root}/capnproto/__init__.py" <<'PYTHON'
from pathlib import Path

import capnp

_SCHEMA_DIRECTORY = Path(__file__).resolve().parent


def load(schema_name: str):
    """Load a bundled Cap'n Proto schema through pycapnp."""
    return capnp.load(str(_SCHEMA_DIRECTORY / f"{schema_name}.capnp"))
PYTHON

mapfile -t flatbuffer_schemas < <(
  find "${schema_root}/flatbuffers" -maxdepth 1 -name '*.fbs' -print | sort
)
flatc \
  -I "${schema_root}/flatbuffers" \
  --cpp \
  --scoped-enums \
  -o "${cpp_root}/flatbuffers" \
  "${flatbuffer_schemas[@]}"
flatc \
  -I "${schema_root}/flatbuffers" \
  --python \
  -o "${python_root}/flatbuffers" \
  "${flatbuffer_schemas[@]}"

cp "${schema_root}/cstructs/"*.h "${cpp_root}/cstructs/"
cp "${schema_root}/cstructs/"*.py "${python_root}/cstructs/"

mapfile -t ros2_idl_schemas < <(
  find "${schema_root}/ros2_idl" -maxdepth 1 -name '*.idl' -print | sort
)
fastddsgen \
  -replace \
  -typeros2 \
  -I "${schema_root}/ros2_idl" \
  -d "${cpp_root}/ros2_cdr" \
  "${ros2_idl_schemas[@]}"

cp \
  "${schema_root}/ros/"*.msg \
  "${python_root}/ros/robotics_benchmark_msgs/_schemas/"
cat > "${python_root}/ros/robotics_benchmark_msgs/__init__.py" <<'PYTHON'
from pathlib import Path

from rosbags.typesys import Stores
from rosbags.typesys import get_types_from_msg
from rosbags.typesys import get_typestore

_SCHEMA_DIRECTORY = Path(__file__).resolve().parent / "_schemas"
_MESSAGES = {
    "BigSensor": "big_sensor.msg",
    "FixedNumericArray": "fixed_numeric_array.msg",
    "ListOfNested": "list_of_nested.msg",
    "ListOfTriplyNested": "list_of_triply_nested.msg",
    "NestedListLevel1": "nested_list_level_1.msg",
    "NestedListLevel2": "nested_list_level_2.msg",
    "SmallFlat": "small_flat.msg",
    "WideFlat": "wide_flat.msg",
}
_TYPE_REPLACEMENTS = {
    "small_flat": "SmallFlat",
    "nested_list_level_1": "NestedListLevel1",
    "nested_list_level_2": "NestedListLevel2",
}


def create_typestore():
    """Create a ROS-independent typestore with all benchmark messages."""
    definitions = {}
    for message_name, filename in _MESSAGES.items():
        text = (_SCHEMA_DIRECTORY / filename).read_text()
        for source, destination in _TYPE_REPLACEMENTS.items():
            text = text.replace(source, destination)
        definitions.update(
            get_types_from_msg(
                text,
                f"robotics_benchmark_msgs/msg/{message_name}",
            )
        )

    typestore = get_typestore(Stores.EMPTY)
    typestore.register(definitions)
    return typestore
PYTHON
