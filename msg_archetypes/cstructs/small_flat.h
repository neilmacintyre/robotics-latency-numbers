#ifndef ROBOTICS_NUMBERS_MSG_ARCHETYPES_SMALL_FLAT_H
#define ROBOTICS_NUMBERS_MSG_ARCHETYPES_SMALL_FLAT_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
  uint64_t timestamp_ns;
  uint32_t sequence;
  float x;
  float y;
  float z;
  double value;
  bool valid;
} SmallFlat;

#endif
