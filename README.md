
# Latency Numbers Every Robotics Engineer Should Know

## Copy

| Size   |  x86 Laptop Median (ms)| Jetson Orin Median (ms) |
|--------|-------------|-----------|
| 1 KB   | 0.0001305   |   |
| 10 KB  | 0.000546    |   |
| 1 MB   | 0.052984    |   |
| 10 MB  | 0.716225    |   |
| 100 MB | 8.54879     |   |

Results collected on:
**CPU**: Intel(R) Core(TM) i5-8350U CPU @ 1.70GHz 6 MiB (L3 Cache)  (`lscpu`)
**RAM MEMCPY bandwidth** ~6,300 MiB/s  (`mbw -n 10 1024`)

## Page fault

| Size   |  x86 Laptop Median (ms)| Jetson Orin Median (ms) |
|--------|-------------|-----------|
| 1 KB   | 0.0001305   |   |
| 10 KB  | 0.000546    |   |
| 1 MB   | 0.052984    |   |
| 10 MB  | 0.716225    |   |
| 100 MB | 8.54879     |   |



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
Unix Domain sockets
TCPROS (ie ros1)
Zenoh
DDS
LCM
(remeber passing a reference is pretty much free)

*[How fast are Linux pipes anyway?](https://mazzo.li/posts/fast-pipes.html)


## Proccess Wake up

Sleep time between wake ups to Time to wake up

- sleeping for 0.01hz can be 10-50 million clock cycles 



[Latency Numbers Every Programmer Should Know](https://gist.github.com/jboner/2841832)

## Message Network Overhead

[The Macroscopic Behavior of the TCP Congestion Avoidance Algorithm](https://courses.cs.duke.edu/fall25/compsci514/readings/mathis-tcpmodel-ccr97.pdf)
[Modeling TCP Latency](https://cseweb.ucsd.edu/~savage/papers/Infocom2000tcp.pdf
[Offload or Overload: A Platform Measurement Study of Mobile Robotic Manipulation Workloads](https://arxiv.org/pdf/2603.18284)


## Clock Syncronization
