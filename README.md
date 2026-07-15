
# Latency Numbers Every Robotics Engineer Should Know

## Copy

| Size   | Median (ms) | Max (ms)  |
|--------|-------------|-----------|
| 1 KB   | 0.0001305   | 0.001252  |
| 10 KB  | 0.000546    | 0.029465  |
| 1 MB   | 0.052984    | 0.282431  |
| 10 MB  | 0.716225    | 1.66273   |
| 100 MB | 8.54879     | 14.6539   |

Results collected on:
CPU: Intel(R) Core(TM) i5-8350U CPU @ 1.70GHz
sysbench memory reports ~20 GB/sec RAM memory bandwidth

## Page fault


## Serilaization Multipliers:
Protobuff
ROS1
ROS2
Cstruct


## Deserilaization Multipliers:
Protobuff
ROS1
ROS2
Cstruct

## IPC Mulitpliers


Pipe
UDX
TCPROS (ie ros1)
Zenoh
DDS
LCM

*[How fast are Linux pipes anyway?](https://mazzo.li/posts/fast-pipes.html)


## Proccess Wake up

Sleep time between wake ups to Time to wake up



[Latency Numbers Every Programmer Should Know](https://gist.github.com/jboner/2841832)