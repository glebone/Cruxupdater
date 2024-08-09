#!/usr/bin/env python3

"""

^..^ CAT Soft - Crux Update Check and clean script 
 ------------------------------------------
 8 Aug 2024 ||  glebone@gmail.com  || Blahodatne on CruxPad


Check for outdated ports and available versions in CRUX Linux.

Usage:
    updatecheck.py --list
    updatecheck.py --available
    updatecheck.py --clean

Options:
    --list            Return a plain list of packages that need to be updated.
    --available       Show all available versions for each package in prt-get diff,
                      marking the version mentioned in prt-get diff in red and installing
                      the new version if available.
    --clean           Clean old built packages and generate a report on the space freed.
"""

import os
import subprocess
import argparse
from termcolor import colored
import shutil

def get_outdated_ports():
    print("Retrieving list of outdated packages...")
    result = subprocess.run(['prt-get', 'diff'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to get the list of outdated ports.")
        return []
    
    raw_output = result.stdout.strip()
    lines = raw_output.split('\n')
    outdated_ports = []

    for line in lines:
        if line.strip() and not line.startswith(('Port', 'Differences', '====', '---')):
            parts = line.split()
            if len(parts) >= 3:
                port_name = parts[0]
                installed_version = parts[1]
                available_version = parts[2]
                outdated_ports.append((port_name, installed_version, available_version))
    
    return outdated_ports

def find_port_directory(port_name):
    possible_dirs = ['/usr/ports/core', '/usr/ports/opt', '/usr/ports/contrib', '/usr/ports/xfce', '/usr/ports/xorg']
    for base_dir in possible_dirs:
        port_dir = os.path.join(base_dir, port_name)
        if os.path.isdir(port_dir):
            return port_dir
    return None

def list_outdated_ports():
    outdated_ports = get_outdated_ports()
    if not outdated_ports:
        print("No ports need to be updated.")
    else:
        for port_name, installed_version, available_version in outdated_ports:
            print(f"{port_name}")

def install_new_version(port_name, pkg_file):
    install_command = ['sudo', 'pkgadd', '-u', pkg_file]
    print(f"Executing: {' '.join(install_command)}")
    result = subprocess.run(install_command, text=True)
    if result.returncode != 0:
        print(f"Failed to install {port_name}.")
        return False
    print(f"Successfully updated {port_name}.")
    return True

def list_available_versions():
    outdated_ports = get_outdated_ports()
    if not outdated_ports:
        print("No ports need to be updated.")
        return

    for port_name, installed_version, available_version in outdated_ports:
        port_dir = find_port_directory(port_name)
        if not port_dir:
            continue

        # List available versions in the directory
        available_versions = []
        for file in os.listdir(port_dir):
            if file.startswith(port_name) and file.endswith('.pkg.tar.gz'):
                available_versions.append(file)

        if available_versions:
            print(f"\n{port_name}:")
            for version in available_versions:
                if available_version in version:
                    print(colored(version, 'red'))
                    # Attempt to install the new version
                    pkg_file = os.path.join(port_dir, version)
                    install_new_version(port_name, pkg_file)
                else:
                    print(version)

def clean_old_packages():
    # Get initial disk usage
    initial_usage = get_disk_usage()
    initial_free_space = get_free_space()

    print(f"Initial free space: {initial_free_space}")

    # Find and delete old packages
    deleted_packages = []
    possible_dirs = ['/usr/ports/core', '/usr/ports/opt', '/usr/ports/contrib', '/usr/ports/xfce', '/usr/ports/xorg']
    for base_dir in possible_dirs:
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.pkg.tar.gz'):
                    file_path = os.path.join(root, file)
                    deleted_packages.append(file_path)
                    os.remove(file_path)

    # Get final disk usage
    final_usage = get_disk_usage()
    final_free_space = get_free_space()

    print(f"Final free space: {final_free_space}")

    # Calculate space freed
    space_freed = final_free_space - initial_free_space

    # Generate report
    with open('clean_report.txt', 'w') as report_file:
        report_file.write("Deleted Packages:\n")
        for package in deleted_packages:
            report_file.write(f"{package}\n")
        report_file.write(f"\nInitial free space: {initial_free_space}G\n")
        report_file.write(f"Final free space: {final_free_space}G\n")
        report_file.write(f"Space freed: {space_freed}G\n")

    print(f"Clean report saved to clean_report.txt")
    print(f"Space freed: {space_freed}G")

def get_disk_usage():
    result = subprocess.run(['df', '-h'], capture_output=True, text=True)
    return result.stdout

def get_free_space():
    result = subprocess.run(['df', '--output=avail', '/usr/ports'], capture_output=True, text=True)
    free_space = result.stdout.splitlines()[1].strip()
    return int(free_space) / 1024 / 1024  # Convert to GB

def main():
    parser = argparse.ArgumentParser(description='Check for outdated ports and available versions in CRUX Linux.')
    parser.add_argument('--list', action='store_true', help='Return a plain list of packages that need to be updated.')
    parser.add_argument('--available', action='store_true', help='Show all available versions for each package, marking the version in prt-get diff in red and installing the new version if available.')
    parser.add_argument('--clean', action='store_true', help='Clean old built packages and generate a report on the space freed.')
    args = parser.parse_args()

    if args.list:
        list_outdated_ports()
    elif args.available:
        list_available_versions()
    elif args.clean:
        clean_old_packages()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
