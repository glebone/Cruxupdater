#!/bin/bash

# Function to check the success of the last command
check_success() {
    if [ $? -ne 0 ]; then
        echo "Error: $1 failed."
        exit 1
    fi
}

# Bring up the wireless interface
ip link set wlp59s0 up
check_success "ip link set wlp59s0 up"

# Start wpa_supplicant
wpa_supplicant -B -i wlp59s0 -c /etc/wpa_supplicant/wpa_supplicant.conf
check_success "wpa_supplicant"

# Start dhcpcd to obtain an IP address
dhcpcd wlp59s0
check_success "dhcpcd"

# Switch to user
su user -c "
    # Start PulseAudio
    pulseaudio --start
    if [ $? -ne 0 ]; then
        echo 'Error: pulseaudio failed.'
        exit 1
    fi

    # Start XFCE
    exec startxfce4
    if [ $? -ne 0 ]; then
        echo 'Error: startxfce4 failed.'
        exit 1
    fi
"

# Check if su command succeeded
check_success "su glebone"

# If all commands succeeded
echo "All commands completed successfully."
