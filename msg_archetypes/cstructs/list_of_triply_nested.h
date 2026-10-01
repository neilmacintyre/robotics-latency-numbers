#ifndef ROBOTICS_NUMBERS_MSG_ARCHETYPES_LIST_OF_TRIPLY_NESTED_H
#define ROBOTICS_NUMBERS_MSG_ARCHETYPES_LIST_OF_TRIPLY_NESTED_H

#include <stddef.h>
#include <stdint.h>

#include "small_flat.h"

typedef struct {
  size_t items_count;
  SmallFlat *items;
} NestedListLevel2;

typedef struct {
  size_t items_count;
  NestedListLevel2 *items;
} NestedListLevel1;

typedef struct {
  uint64_t timestamp_ns;
  uint32_t sequence;
  size_t items_count;
  NestedListLevel1 *items;
} ListOfTriplyNested;

#endif
