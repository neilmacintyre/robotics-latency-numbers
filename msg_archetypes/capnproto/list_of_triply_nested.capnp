@0xc79ad510e46f2b83;

using SmallFlat = import "small_flat.capnp".SmallFlat;

struct NestedListLevel2 {
  items @0 :List(SmallFlat);
}

struct NestedListLevel1 {
  items @0 :List(NestedListLevel2);
}

struct ListOfTriplyNested {
  timestampNs @0 :UInt64;
  sequence @1 :UInt32;
  items @2 :List(NestedListLevel1);
}
