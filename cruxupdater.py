#!/usr/bin/env python3

"""
 ^..^ CAT Soft - Crux Updater Script 
 ------------------------------------------
 8 Aug 2024 ||  glebone@gmail.com  || Blahodatne on CruxPad

Update outdated ports in CRUX Linux.

Usage:
    update_ports.py [-n NUM_PORTS] [--skip-md5] [--skip PACKAGE [PACKAGE ...]] [--list PACKAGE [PACKAGE ...]]

Options:
    -n NUM_PORTS         Number of ports to update (default: update all).
    --skip-md5           Skip MD5 check (default: generate new MD5 checksum).
    --skip PACKAGE       List of packages to skip (default: empty).
    --list PACKAGE       List of specific packages to update (default: update all outdated packages).
"""

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
    possible_dirs = ['/usr/ports/core', '/usr/ports/opt', '/usr/ports/contrib', '/usr/ports/xfce', '/usr/ports/xorg', '/usr/ports/xfce4']
    for base_dir in possible_dirs:
        port_dir = os.path.join(base_dir, port_name)
        if os.path.isdir(port_dir):
            print(f"Found directory for port {port_name}: {port_dir}")
            return port_dir
    print(f"Directory for port {port_name} not found.")
    return None

def update_pkgfile_with_new_md5(port_dir):
    print(f"Updating Pkgfile with new MD5 checksum in {port_dir}...")
    md5sum_result = subprocess.run(['pkgmk', '-um'], cwd=port_dir, capture_output=True, text=True)
    
    print(f"Command executed: pkgmk -um in {port_dir}")
    print(f"STDOUT: {md5sum_result.stdout}")
    print(f"STDERR: {md5sum_result.stderr}")
    
    if "Source file" in md5sum_result.stderr and "not found" in md5sum_result.stderr:
        print("Source file not found. Attempting to download the source with pkgmk -d...")
        
        # Run pkgmk -d without capturing output, so progress is shown
        download_result = subprocess.run(['pkgmk', '-d'], cwd=port_dir)
        
        if download_result.returncode == 0:
            print("Source file downloaded successfully. Updating MD5 checksum...")
            # After downloading, update the MD5 checksum
            md5sum_result = subprocess.run(['pkgmk', '-um'], cwd=port_dir, capture_output=True, text=True)
            print(f"Retry STDOUT: {md5sum_result.stdout}")
            print(f"Retry STDERR: {md5sum_result.stderr}")
            if md5sum_result.returncode != 0:
                print(f"Failed to update MD5 checksum in {port_dir} after downloading the source.")
                return False
        else:
            print(f"Failed to download source files in {port_dir}.")
            return False
    
    print(f"Updated MD5 checksum in {port_dir}/Pkgfile")
    return True

def check_and_download_source(port_dir):
    print(f"Checking and downloading source files in {port_dir}...")
    result = subprocess.run(['pkgmk', '-d'], cwd=port_dir, text=True)
    if result.returncode != 0:
        print(f"Failed to download source files in {port_dir}. Attempting to regenerate MD5 checksums...")
        if not update_pkgfile_with_new_md5(port_dir):
            return False
        result = subprocess.run(['pkgmk', '-d'], cwd=port_dir, text=True)
        if result.returncode != 0:
            print(f"Failed to download source files in {port_dir} after regenerating MD5 checksums.")
            return False
    print(f"Successfully downloaded source files in {port_dir}.")
    return True

def update_port(port_name, installed_version, available_version, skip_md5=False):
    port_dir = find_port_directory(port_name)
    if not port_dir:
        return False

    os.chdir(port_dir)
    if skip_md5:
        skip_md5_check(port_dir)
    else:
        if not update_pkgfile_with_new_md5(port_dir):
            return False
    
    # Check if the source file exists, if not download it
    if not check_and_download_source(port_dir):
        return False
    
    print(f"Building the package for {port_name} in {port_dir}...")
    result = subprocess.run(['sudo', 'pkgmk', '-if'], text=True)
    if result.returncode != 0:
        print(f"Failed to build {port_name}.")
        return False

    # Check for the package file in both 'pkg' directory and current directory
    pkg_files = []
    pkg_dir = os.path.join(port_dir, 'pkg')
    if os.path.exists(pkg_dir):
        pkg_files = [f for f in os.listdir(pkg_dir) if f.startswith(f'{port_name}#') and f.endswith('.pkg.tar.gz')]
    if not pkg_files:
        pkg_files = [f for f in os.listdir(port_dir) if f.startswith(f'{port_name}#') and f.endswith('.pkg.tar.gz')]

    if not pkg_files:
        print(f"No package file found for {port_name}.")
        return False
    
    # Find the latest package file
    pkg_files.sort(reverse=True)
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
    parser.add_argument('--skip-md5', action='store_true', help='skip MD5 check (default: generate new MD5 checksum)')
    parser.add_argument('--skip', nargs='+', help='list of packages to skip', default=[])
    parser.add_argument('--list', nargs='+', help='list of specific packages to update', default=None)
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

    # Filter out ports to skip
    ports_to_update = [port for port in outdated_ports if port[0] not in args.skip]

    # Filter out ports not in the list if the list is specified
    if args.list is not None:
        ports_to_update = [port for port in ports_to_update if port[0] in args.list]

    # Determine the number of ports to update
    num_ports_to_update = args.n if args.n else len(ports_to_update)
    ports_to_update = ports_to_update[:num_ports_to_update]

    updated_ports = []

    for port_name, installed_version, available_version in ports_to_update:
        print("\n########################################")
        print(f"### Updating {port_name} from version {installed_version} to {available_version}...")
        print("########################################")
        if update_port(port_name, installed_version, available_version, args.skip_md5):
            updated_ports.append(port_name)

    print("\nSummary:")
    summary_table = [["Port Name", "Status"]]
    for port_name, installed_version, available_version in outdated_ports:
        if port_name in args.skip:
            status = "Skipped"
        elif args.list is not None and port_name not in args.list:
            status = "Not in list"
        else:
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
