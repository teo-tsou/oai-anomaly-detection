# AI/ML-Driven Anomaly Detection & RAN Slicing/RRC Release in O-RAN enabled OAI

![alt text](https://github.com/teo-tsou/oai-anomaly-detection/blob/main/arch-setup.png)

**DEMO on YouTube:**


[![DEMO](https://img.youtube.com/vi/4hx1mAvhXMY/0.jpg)]([https://www.youtube.com/watch?v=2scoAJRxJrY](https://youtu.be/4hx1mAvhXMY))


## Repository Structure

- **conf**
  - Contains configuration files for:
    - gNB
    - UE
    - Multi-UE scripts

- **generate-ue-traffic**
  - Python scripts for generating UE traffic based on the KDDCUP’99 dataset using Scapy. This involves replaying the dataset for 2 UEs.

- **notebooks**
  - Jupyter notebooks (.ipynb files) that include:
    - Training and evaluation of various AI/ML models on the classification of attacks/normal activities using the KDDCUP’99 dataset.
    - Analysis of the random forest model.

- **slicing-cn**
  - Docker-compose files for deploying the multi-slice UPF (1&2) core network.
  - The UPF images are sourced from `ttsourdinis/custom-upf`.
  - These images incorporate Anomaly Detection Servers (ADS) functionality within the UPFs.

- **xapp_rc_slice_ctrl.c**
  - The xApp that:
    - Enforces RB (Resource Block) resources to end-users based on the anomaly ratio obtained from ADS.
    - Triggers RRC (Radio Resource Control) UE connection release for identified attackers.

- **README.md**
  - Contains an overview of the project and setup instructions.

- **arch-setup.png**
  - An architectural diagram illustrating the setup.

## Reproducibility Instructions
 
### Start the Core Network
  ```bash
  cd slicing-cn
  docker compose -f docker-compose-slicing-basic-nrf.yaml up -d
  ```

### Compile FlexRIC
  ```bash
  git clone https://gitlab.eurecom.fr/mosaic5g/flexric
  cd flexric
  git checkout slicing-spring-of-code
  cp <path-to/oai-anomaly-detection/xapp_rc_slice_ctrl.c> /examples/xApp/c/ctrl/
  ```
  ```bash
  mkdir build && cd build && cmake -DXAPP_MULTILANGUAGE=OFF .. && make -j8 && sudo make install
  ```

### Compile OAI and build telnet libraries for RRC Release trigger.
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

### Start nearRT-RIC
  ```bash
  cd flexric/build/examples/ric
  ./nearRT-RIC 
  ```

### Start gNB-mono
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo ./nr-softmodem -O <path-to/oai-anomaly-detection/gnb.conf> --sa --rfsim -E --gNBs.[0].min_rxtxtime 6  --telnetsrv --telnetsrv.shrmod rrc
  ```

  ### Start RC xApp
  ```bash
  cd flexric/build/examples/xApp/c/ctrl
  ./xapp_rc_slice_ctrl
  ```

  ### Start the Anomaly Detection Servers in the UPF:
 
  #### For UPF-Slice1:
  ```bash
  docker exec -ti oai-upf-slice1 bash
  python3 anomaly-detection-slice1.py
  ```

  #### For UPF-Slice2:
  ```bash
  docker exec -ti oai-upf-slice2 bash
  python3 anomaly-detection-slice2.py
  ```

Both Anomaly Detectors should be connected to the xapps.

### Start the UEs

#### Start UE#1
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo <path-to/multi-ue.sh> -c1 -e  # create namespace
  sudo LD_LIBRARY_PATH=. ./nr-uesoftmodem --rfsimulator.serveraddr 10.201.1.100 -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa -O <path-to/oai-anomaly-detection/conf/ue_1.conf> -E
  ```

#### Start UE#2
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo <path-to/multi-ue.sh> -c2 -e  # create namespace
  sudo LD_LIBRARY_PATH=. ./nr-uesoftmodem --rfsimulator.serveraddr 10.202.1.100 -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa -O <path-to/oai-anomaly-detection/ue_2.conf> -E
  ```

### Generate UE Traffic from the real-world dataset (KDDCUP’99) via Scapy:

#### For UE1:    
 ```bash
ip netns exec ue1 bash
cd <path-to/oai-anomaly-detection/generate-ue-traffic>
python3 generate-ue1.py
```

#### For UE2:    
 ```bash
ip netns exec ue2 bash
cd <path-to/oai-anomaly-detection/generate-ue-traffic>
python3 generate-ue2.py
```

### Generate DoS Attack using Hping3:
  
#### Small-size packet attack:

`hping3 -S -d 100 -a 12.2.1.2 12.2.1.1`

#### Medium-size packet attack:

`hping3 -S -d 100000 -a 12.2.1.2 12.2.1.1 --flood`

#### Huge-size packet attack (this might cause RAN to fail):

`hping3 -S -d 1000000000000000000 -a 12.2.1.2 12.2.1.1 --flood`


### Observe the XApp logs:

Watch how the RBs are shared when starting the malicious packets via Scapy (generate-ue-traffic). Also, observe the RRC UE release during the DoS attacks.

