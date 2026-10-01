@0xb96f27d4a103ec58;

struct FixedNumericArray {
  timestampNs @0 :UInt64;
  sequence @1 :UInt32;

  # Producers and consumers must enforce exactly 36 elements.
  values @2 :List(Float64);
}
