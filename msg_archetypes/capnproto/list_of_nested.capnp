@0xeab71384cd926f50;

using SmallFlat = import "small_flat.capnp".SmallFlat;

struct ListOfNested {
  timestampNs @0 :UInt64;
  sequence @1 :UInt32;
  samples @2 :List(SmallFlat);
}
