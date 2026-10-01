#ifndef ROBOTICS_NUMBERS_MSG_ARCHETYPES_FIXED_NUMERIC_ARRAY_H
#define ROBOTICS_NUMBERS_MSG_ARCHETYPES_FIXED_NUMERIC_ARRAY_H

#include <stdint.h>

typedef struct {
  uint64_t timestamp_ns;
  uint32_t sequence;
  double values[36];
} FixedNumericArray;

#endif
