import pandas as pd
from scapy.all import *
import time
import random
from scapy.contrib.gtp import GTP_U_Header, GTPEchoRequest, GTPEchoResponse


# Load data with the same column names as before
column_names = ["duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in", "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations", "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login", "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate", "dst_host_count", "d>
test_df = pd.read_csv('Test.txt', header=None, names=column_names)

def generate_packet(row):
    max_payload_size = 1400
    service_ports = {
        'http': 80, 'https': 443, 'ftp': 21, 'ftp_data': 20, 'smtp': 25, 'pop_3': 110,
        'telnet': 23, 'imap4': 143, 'ssh': 22, 'domain': 53, 'gopher': 70,
        'systat': 11, 'daytime': 13, 'netstat': 15, 'echo': 7, 'discard': 9,
        'X11': 6000, 'urp_i': 5001, 'auth': 113, 'uucp_path': 117,
        'login': 513, 'shell': 514, 'printer': 515, 'efs': 520, 'temp': 525,
        'courier': 530, 'conference': 531, 'netnews': 532, 'netbios_ns': 137,
        'netbios_dgm': 138, 'netbios_ssn': 139, 'klogin': 543, 'kshell': 544,
        'ldap': 389, 'exec': 512, 'biff': 512, 'whois': 43, 'sql_net': 150,
        'ntp_u': 123, 'tftp_u': 69, 'IRC': 194, 'z39.50': 210,
        'pop_2': 109, 'sunrpc': 111, 'vmnet': 175, 'nntp': 119, 'private': 333, 'domain_u': 332,
        'uucp': 334, 'supdup': 335, 'pm_dump':336, 'mtp':337,  'other': 0  # Reserved for any non-specific services
    }
    
    flag_mapping = {
        'REJ': 'R',       # Rejected (usually not directly map to a TCP flag but can simulate with RST)
        'SF': 'PA',       # Standard data transmission (PSH, ACK)
        'RSTO': 'R',      # Connection reset with no payload
        'S0': 'S',        # Initial connection request (SYN)
        'RSTR': 'RA',     # Reset with acknowledgment
        'SH': 'S',        # SYN High - typically not a standard flag, assuming SYN for simulation
        'S3': 'SA',       # SYN, ACK - Part of a three-way handshake
        'S2': 'SA',       # Same as S3, for simplification
        'S1': 'SA',       # Same as S2, further simplification
        'RSTOS0': 'RS',   # Reset during SYN
        'OTH': ''         # No flags set
    }

    protocol = row['protocol_type'].lower()
    service = row['service']
    flag = flag_mapping.get(row['flag'], '')
    src_bytes = row['src_bytes']
    dst_bytes = row['dst_bytes']
    
    port = service_ports.get(service, 0)
    src_payload = 'X' * min(src_bytes, max_payload_size)

    if protocol == 'tcp':
        inner_packet = IP(src= "12.1.1.130", dst="192.168.70.145")/TCP(dport=port, flags=flag)/Raw(load=src_payload)
    elif protocol == 'udp':
        inner_packet = IP(src= "12.1.1.130", dst="192.168.70.145")/UDP(dport=port)/Raw(load=src_payload)
    else:
        inner_packet = IP(src= "12.1.1.130", dst="192.168.70.145")/ICMP()  # Default for other protocols
    
    # Encapsulate in GTP-U packet
    #gtp_packet = IP(src= "12.1.1.130", dst="12.1.1.129")/UDP(sport=2152, dport=2152)/GTP_U_Header(teid=1)/inner_packet

    # Handling response packet if there is any payload to respond with
    if dst_bytes > 0:
        dst_payload = 'X' * min(dst_bytes, max_payload_size)
        response_inner_packet = IP(src="192.168.70.145", dst="12.1.1.130")/TCP(sport=port, dport=1024, flags='PA')/Raw(load=dst_payload)
        # Encapsulate response in GTP-U
        #response_gtp_packet = IP(src= "12.1.1.130", dst="12.1.1.129")/UDP(sport=2152, dport=2152)/GTP_U_Header(teid=1)/response_inner_packet
        return (inner_packet, response_inner_packet)
    else:
        return (inner_packet, None)

def simulate_traffic(dataframe):
    for index, row in dataframe.iterrows():
        packet, response_packet = generate_packet(row)
        print(f"Sending GTP encapsulated packet with size: {len(bytes(packet))}")
        send(packet, iface="oaitun_ue1")  # Sending the main packet on the correct interface
        if response_packet:
            print(f"Sending GTP encapsulated response packet with size: {len(bytes(response_packet))}")
            send(response_packet, iface="oaitun_ue1")
        time.sleep(random.uniform(0.1, 1.0))  # Simulated traffic timing

simulate_traffic(test_df)
