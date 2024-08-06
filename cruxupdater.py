#!/usr/bin/env python3

import os
import subprocess
import argparse
from datetime import datetime
from tabulate import tabulate

def get_outdated_ports():
    print("Retrieving list of outdated packages...")
    result = subprocess.run(['prt-get', 'diff'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to get the list of outdated ports.")
        return []
    
    print("Raw output from prt-get diff:")
    raw_output = result.stdout.strip()
    print(raw_output)

    outdated_ports = []
    lines = raw_output.split('\n')
    for line in lines:
        print(f"Processing line: {line}")
        if line.strip() and not line.startswith(('Port', 'Differences', '====', '---')):
            parts = line.split()
            print(f"Splitted parts: {parts}")
            if len(parts) >= 3:
                port_name = parts[0]
                installed_version = parts[1]
                available_version = parts[2]
                outdated_ports.append((port_name, installed_version, available_version))
                print(f"Added port: {port_name}, installed version: {installed_version}, available version: {available_version}")
    
    return outdated_ports

def find_port_directory(port_name):
    possible_dirs = ['/usr/ports/core', '/usr/ports/opt', '/usr/ports/contrib', '/usr/ports/xfce', '/usr/ports/xorg']
    for base_dir in possible_dirs:
        port_dir = os.path.join(base_dir, port_name)
        if os.path.isdir(port_dir):
            print(f"Found directory for port {port_name}: {port_dir}")
            return port_dir
    print(f"Directory for port {port_name} not found.")
    return None

def skip_md5_check(port_dir):
    pkgfile_path = os.path.join(port_dir, 'Pkgfile')
    if os.path.exists(pkgfile_path):
        with open(pkgfile_path, 'r') as file:
            lines = file.readlines()
        with open(pkgfile_path, 'w') as file:
            for line in lines:
                if not line.strip().startswith('md5sums'):
                    file.write(line)
        print(f"Skipped MD5 check in {pkgfile_path}")

def update_port(port_name, installed_version, available_version):
    port_dir = find_port_directory(port_name)
    if not port_dir:
        return False

    os.chdir(port_dir)
    skip_md5_check(port_dir)
    print(f"Building the package for {port_name} in {port_dir}...")
    result = subprocess.run(['sudo', 'pkgmk', '-if'], text=True)
    if result.returncode != 0:
        print(f"Failed to build {port_name}.")
        return False

    # Check for the package file in both 'pkg' directory and current directory
    pkg_files = []
    pkg_dir = os.path.join(port_dir, 'pkg')
    if os.path.exists(pkg_dir):
        pkg_files = [f for f in os.listdir(pkg_dir) if f.startswith(f'{port_name}#')]
    if not pkg_files:
        pkg_files = [f for f in os.listdir(port_dir) if f.startswith(f'{port_name}#')]

    if not pkg_files:
        print(f"No package file found for {port_name}.")
        return False
    
    pkg_file = os.path.join(port_dir, pkg_files[0])
    print(f"Would install {pkg_file}")
    print(f"Updating {port_name} from version {installed_version} to {available_version}")

    # Actual installation
    install_command = ['sudo', 'pkgadd', '-u', pkg_file]
    print(f"Executing: {' '.join(install_command)}")
    result = subprocess.run(install_command, text=True)
    if result.returncode != 0:
        print(f"Failed to install {port_name}.")
        return False
    
    print(f"Successfully updated {port_name}.")
    return True

def main():
    parser = argparse.ArgumentParser(description='Update outdated ports in CRUX Linux.')
    parser.add_argument('-n', type=int, help='number of ports to update (default: update all)')
    args = parser.parse_args()

    outdated_ports = get_outdated_ports()
    if not outdated_ports:
        print("No ports need to be updated.")
        return

    print("\nPorts that need to be updated:")
    table = [["Port Name", "Installed Version", "Available Version"]]
    for port_name, installed_version, available_version in outdated_ports:
        table.append([port_name, installed_version, available_version])
    print(tabulate(table, headers="firstrow"))

    # Determine the number of ports to update
    num_ports_to_update = args.n if args.n else len(outdated_ports)
    ports_to_update = outdated_ports[:num_ports_to_update]

    updated_ports = []

    for port_name, installed_version, available_version in ports_to_update:
        print("\n########################################")
        print(f"### Updating {port_name} from version {installed_version} to {available_version}...")
        print("########################################")
        if update_port(port_name, installed_version, available_version):
            updated_ports.append(port_name)

    print("\nSummary:")
    summary_table = [["Port Name", "Status"]]
    for port_name, installed_version, available_version in ports_to_update:
        status = "Updated" if port_name in updated_ports else "Failed"
        summary_table.append([port_name, status])
    
    print(tabulate(summary_table, headers="firstrow"))

    # Save report to file
    report_filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-update.txt")
    with open(report_filename, 'w') as report_file:
        report_file.write(tabulate(summary_table, headers="firstrow"))
    
    print(f"\nReport saved to {report_filename}")

if __name__ == '__main__':
    main()
