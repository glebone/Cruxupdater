#!/usr/bin/env python3

"""
^..^ CAT Soft - Crux Startup Script 
------------------------------------------
16 Aug 2024 || glebone@gmail.com || Blahodatne on CruxPad

Setup wireless, start wpa_supplicant, start dhcpcd, switch to user, 
start PulseAudio, and start XFCE.

Usage:
    startup_crux.py [--place=dacha|home]

Options:
    --place    Specify the location to update the wpa_supplicant configuration.
               - dacha: Updates for NeoMars5G network.
               - home: Updates for cathost network.
               If no place is specified, the wpa_supplicant configuration is not updated.
"""

import os
import sys

def update_wpa_supplicant(place):
    """Update the wpa_supplicant.conf based on the place parameter."""
    config = (
        "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=wheel\n"
        "update_config=1\n\n"
    )

    if place == "dacha":
        network_config = (
            'network={\n'
            '    ssid="NeoMars5G"\n'
            '    psk="krysovus"\n'
            '}\n'
        )
    elif place == "home":
        network_config = (
            'network={\n'
            '    ssid="cathost"\n'
            '    psk="krysovus"\n'
            '}\n'
        )
    else:
        print("Error: Invalid place. Please use --place=dacha or --place=home.")
        sys.exit(1)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
        f.write(config)
        f.write(network_config)

    print(f"wpa_supplicant.conf updated for {place}")

def main():
    place = None
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("--place="):
            place = sys.argv[1].split("=")[-1]

    if place:
        update_wpa_supplicant(place)

if __name__ == "__main__":
    main()