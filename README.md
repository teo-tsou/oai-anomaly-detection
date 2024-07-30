# OAI Anomaly Detection

![alt text](https://github.com/teo-tsou/oai-anomaly-detection/blob/master/explanatory-second.png)

## 6.2 Slicing Configuration

- slice #1: ssT=1, sD=1
- slice #2: ssT=1, sD=5
 
* Start the CN
  ```bash
  cd slicing-cn
  docker compose -f docker-compose-slicing-basic-nrf.yaml up -d
  ```

* Compile FlexRIC
  ```bash
  git clone https://gitlab.eurecom.fr/mosaic5g/flexric
  cd flexric
  git checkout slicing-spring-of-code
  ```
  ```bash
  mkdir build && cd build && cmake -DXAPP_MULTILANGUAGE=OFF .. && make -j8 && sudo make install
  ```

* Compile OAI and build telnet libraries for RRC Release trigger.
  ```bash
  git clone https://gitlab.eurecom.fr/oai/openairinterface5g
  cd openairinterface5g
  git checkout slicing-spring-of-code
  cd cmake_targets
  ./build_oai -c -C -w SIMU --gNB --nrUE --build-e2 --ninja
  cd ../
  git checkout develop
  cd cmake_targets
  ./build_oai --build-lib telnetsrv
  ```

* Start nearRT-RIC
  ```bash
  cd flexric/build/examples/ric
  ./nearRT-RIC 
  ```

* Start gNB-mono
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo ./nr-softmodem -O <path-to/oai-workshops/oam/conf/slicing_demo/gnb.conf> --sa --rfsim -E
  ```

  * Start RC xApp
  ```bash
  cd flexric/build/examples/xApp/c/ctrl
  ./xapp_rc_slice_ctrl
  ```

  * Start the Anomaly Detection Servers in the UPF:
 
  * For UPF-Slice1:
  ```bash
  cd flexric/build/examples/xApp/c/ctrl
  python3 anomaly-detection-slice2.py
  ```

  * For UPF-Slice2:
  ```bash
  docker exec -ti oai-upf-slice2 bash
  python3 anomaly-detection-slice2.py
  ```

* Start UE#1
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo <path-to/multi-ue.sh> -c1 -e  # create namespace
  sudo LD_LIBRARY_PATH=. ./nr-uesoftmodem --rfsimulator.serveraddr 10.201.1.100 -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa -O <path-to/oai-workshops/oam/conf/slicing_demo/ue_1.conf> -E
  ```

* Start UE#2
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo <path-to/multi-ue.sh> -c2 -e  # create namespace
  sudo LD_LIBRARY_PATH=. ./nr-uesoftmodem --rfsimulator.serveraddr 10.202.1.100 -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa -O <path-to/oai-workshops/oam/conf/slicing_demo/ue_2.conf> -E
  ```

* Start KPM xApp (optional, to check if the thp is equal to the one in iperf3 logs)
  ```bash
  cd flexric/build/examples/xApp/c/monitor
  ./xapp_kpm_moni
  ```

* Start iperf for UE#1
  - terminal #1
  ```bash
  sudo ip netns exec ue1 bash
  ifconfig  # get UE IP address on interface oaitun_ue1
  iperf3 -i1 -s
  ```

  - terminal #2
  ```bash
  cd <path-to/oai-cn5g-fed/docker-compose>
  docker exec -t oai-ext-dn iperf3 -c <UE-IP-address> -t60 -B 192.168.70.145 -i1  # ip address 12.2.1.0/25
  ```

* Start iperf for UE#2
  - terminal #3
  ```bash
  sudo ip netns exec ue2 bash
  ifconfig  # get UE IP address on interface oaitun_ue1
  iperf3 -i1 -s
  ```

  - terminal #4
  ```bash
  cd <path-to/oai-cn5g-fed/docker-compose>
  docker exec -t oai-ext-dn iperf3 -c <UE-IP-address> -t60 -B 192.168.70.145 -i1  # ip address 12.1.1.128/25
  ```

At this point, you should se max thp is at 100 Mbps, split equally 50/50% between UEs.

* Start RC xApp
  ```bash
  cd flexric/build/examples/xApp/c/ctrl
  ./xapp_rc_slice_ctrl
  ```

RC Control message is sent to gNB-mono, and you should see in its logs:
```bash
[NR_MAC]   [E2-Agent]: RC CONTROL rx, RIC Style Type 2, Action ID 6
[NR_MAC]   Add default DL slice id 99, label default, sst 0, sd 0, slice sched algo NVS_CAPACITY, pct_reserved 0.05, ue sched algo nr_proportional_fair_wbcqi_dl
[NR_MAC]   configure slice 0, label SST1SD1, Min_PRB_Policy_Ratio 0
[NR_MAC]   configure slice 0, label SST1SD1, Dedicated_PRB_Policy_Ratio 70
[NR_MAC]   add DL slice id 1, label SST1SD1, slice sched algo NVS_CAPACITY, pct_reserved 0.66, ue sched algo nr_proportional_fair_wbcqi_dl
[NR_MAC]   Matched slice, Add UE rnti 0x1013 to slice idx 0, sst 0, sd 0
[NR_MAC]   Matched slice, Add UE rnti 0x1013 to slice idx 1, sst 1, sd 1
[NR_MAC]   configure slice 1, label SST1SD5, Min_PRB_Policy_Ratio 0
[NR_MAC]   configure slice 1, label SST1SD5, Dedicated_PRB_Policy_Ratio 30
[NR_MAC]   add DL slice id 2, label SST1SD5, slice sched algo NVS_CAPACITY, pct_reserved 0.28, ue sched algo nr_proportional_fair_wbcqi_dl
[NR_MAC]   Matched slice, Add UE rnti 0x9b7f to slice idx 0, sst 0, sd 0
[NR_MAC]   Matched slice, Add UE rnti 0x9b7f to slice idx 2, sst 1, sd 5
[E2-AGENT]: CONTROL ACKNOWLEDGE tx
[NR_MAC]   Frame.Slot 896.0
```
and the thp of 100 Mbps is split 70/30% between UEs.
iperf can be run again, and the thp should remain divided 70/30%.
