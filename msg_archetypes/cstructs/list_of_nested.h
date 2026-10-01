#ifndef ROBOTICS_NUMBERS_MSG_ARCHETYPES_LIST_OF_NESTED_H
#define ROBOTICS_NUMBERS_MSG_ARCHETYPES_LIST_OF_NESTED_H

#include <stddef.h>
#include <stdint.h>

#include "small_flat.h"

typedef struct {
  uint64_t timestamp_ns;
  uint32_t sequence;
  size_t samples_count;
  SmallFlat *samples;
} ListOfNested;

#endif
