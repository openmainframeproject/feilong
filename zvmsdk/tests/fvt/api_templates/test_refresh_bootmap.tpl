{'info':
        {
            "fcpchannel": ['5d71'],
            "wwpn": ['5005076802100c1a', '5005076802200c1b'],
            "lun": '0000000000000000',
            "transportfiles": "/path/to/transportfiles",
            "guest_networks": [
                {   
                    "ip_addr": "192.168.95.10",
                    "dns_addr": ["9.0.2.1", "9.0.3.1"],
                    "gateway_addr": "192.168.95.1",
                    "cidr": "192.168.95.0/24",
                    "nic_vdev": "1000",
                    "mac_addr": "02:00:00:12:34:56",
                    "nic_id": "111-222-333",
                    "osa_device": "8080",
                    "hostname": "hostname"
                },
                {
                    "ip_addr": "192.168.95.11",
                    "gateway_addr": "192.168.95.1",
                    "cidr": "192.168.95.0/24",
                    "nic_vdev": "2000",
                    "mac_addr": "02:00:00:12:34:78",
                    "nic_id": "444-555-666"
                }
            ],
        }
}
