@0xf8c05a31be749d62;

struct BigSensor {
  timestampNs @0 :UInt64;
  sequence @1 :UInt32;
  width @2 :UInt32;
  height @3 :UInt32;
  rowStride @4 :UInt32;
  encoding @5 :Text;
  data @6 :Data;
}
