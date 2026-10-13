# AI/ML-Driven Anomaly Detection & RAN Slicing/RRC Release in O-RAN enabled OAI

If you find this repository useful in your research, please consider citing the following paper:

```
@inproceedings{10.1145/3636534.3697311,
  author = {Tsourdinis, Theodoros and Makris, Nikos and Korakis, Thanasis and Fdida, Serge},
  title = {AI-Driven Network Intrusion Detection and Resource Allocation in Real-World O-RAN 5G Networks},
  year = {2024},
  isbn = {9798400704895},
  publisher = {Association for Computing Machinery},
  address = {New York, NY, USA},
  url = {https://doi.org/10.1145/3636534.3697311},
  doi = {10.1145/3636534.3697311},
  booktitle = {Proceedings of the 30th Annual International Conference on Mobile Computing and Networking},
  pages = {1842--1849},
  numpages = {8},
  keywords = {5G, O-RAN, security, AI/ML, slicing, OAI, OpenAirInterface, FlexRIC},
  location = {Washington D.C., DC, USA},
  series = {ACM MobiCom '24}
}
```


![alt text](https://github.com/teo-tsou/oai-anomaly-detection/blob/main/arch-setup.png)

**DEMO on YouTube:**


[![Demo Video](https://img.youtube.com/vi/4hx1mAvhXMY/0.jpg)](https://youtu.be/4hx1mAvhXMY)


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
  cp <path-to/oai-anomaly-detection/xapp_rc_slice_ctrl.c> examples/xApp/c/ctrl/
  ```
  ```bash
  mkdir build && cd build && cmake -DXAPP_MULTILANGUAGE=OFF .. && make -j8 && sudo make install
  ```

### Compile OAI and build telnet libraries for RRC Release trigger.
  ```bash
  git clone https://gitlab.eurecom.fr/oai/openairinterface5g
  cd openairinterface5g
  git checkout slicing-spring-of-code
  # Apply the slice-control concurrency fix before building the gNB (see note below)
  git apply ../patches/0001-fix-slice-ctrl-race-and-null-rrc-ctx.patch
  cd cmake_targets
  ./build_oai -I
  ./build_oai -c -C -w SIMU --gNB --nrUE --build-e2 --ninja
  cd ../
  git checkout 243c985af86f857c28d14c2bb25e54e223b07a00
  cd cmake_targets
  ./build_oai --build-lib telnetsrv
  ```

  > **Note — slice-control race fix (`patches/0001-fix-slice-ctrl-race-and-null-rrc-ctx.patch`):**
  > Without this patch the gNB can segfault when the xApp sends its first slice
  > reconfiguration (`CONTROL-REQUEST`), typically seen when the second UE / second
  > Anomaly Detection Server comes up. The slice structures
  > (`pre_processor_dl.slices`) are mutated by the MAC scheduler and the RRC UE
  > setup/modify/release handlers under `sched_lock`, but the E2 slice-control
  > handler (`add_mod_rc_slice`) only took `UE_info.mutex`, so a reconfiguration
  > could free/rebuild the slices while another thread was walking them
  > (use-after-free). The patch makes `add_mod_rc_slice` also take `sched_lock`
  > (outer, matching the scheduler's lock order) and guards an unchecked
  > `rrc_gNB_get_ue_context_by_rnti_any_du()` return against `NULL`.
  > The patch targets the `slicing-spring-of-code` branch and must be applied
  > before the gNB build step above (the `telnetsrv` build does not rebuild
  > `nr-softmodem`).

### Start nearRT-RIC
  ```bash
  cd flexric/build/examples/ric
  ./nearRT-RIC 
  ```

### Start gNB-mono
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo ./nr-softmodem -O <path-to/oai-anomaly-detection/conf/gnb.conf> --sa --rfsim -E --gNBs.[0].min_rxtxtime 6  --telnetsrv --telnetsrv.shrmod rrc
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
  python3 anomaly-detection-server-slice1.py
  ```

  #### For UPF-Slice2:
  ```bash
  docker exec -ti oai-upf-slice2 bash
  python3 anomaly-detection-server-slice2.py
  ```

Both Anomaly Detectors should be connected to the xapps.

### Start the UEs

#### Start UE1
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo <path-to/multi-ue.sh> -c1 -e  # create namespace
  ip netns exec ue1 bash # enter in the namespace
  sudo LD_LIBRARY_PATH=. ./nr-uesoftmodem --rfsimulator.serveraddr 10.201.1.100 -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa -O <path-to/oai-anomaly-detection/conf/ue_1.conf> -E
  ```

#### Start UE2
  ```bash
  cd openairinterface5g/cmake_targets/ran_build/build
  sudo <path-to/multi-ue.sh> -c2 -e  # create namespace
  ip netns exec ue1 bash # enter in the namespace
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
sudo ip route add 192.168.70.145 dev oaitun_ue1
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

