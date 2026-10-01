#ifndef ROBOTICS_NUMBERS_MSG_ARCHETYPES_BIG_SENSOR_H
#define ROBOTICS_NUMBERS_MSG_ARCHETYPES_BIG_SENSOR_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
  uint64_t timestamp_ns;
  uint32_t sequence;
  uint32_t width;
  uint32_t height;
  uint32_t row_stride;
  const char *encoding;
  size_t data_size;
  uint8_t *data;
} BigSensor;

#endif
