#!/usr/bin/env python3
import hashlib
import os
import sys
import time
import logging
import socket  # Import the entire socket module
from json import loads
from rich.console import Console
from rich.logging import RichHandler

# Setup logging with rich handler
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, console=console)],
)

# Constants
DEFAULT_NODE_ADDRESS = "203.86.195.49"
DEFAULT_NODE_PORT = 2850
MAX_RETRIES = 5  # Maximum retries before giving up

# Variables to track accepted and rejected shares
accepted_shares = 0
rejected_shares = 0


def current_time():
    """Return the current local time as a string formatted as HH:MM:SS."""
    return time.strftime("%H:%M:%S", time.localtime())


def get_user_input():
    """Get username, mining key, and difficulty preference from the user."""
    username = "turjaun"  # Allow user input for username
    mining_key = "turjaun12"
    diff_choice = "y"

    # Set default to True for lower difficulty if no input is provided
    use_lower_diff = True if diff_choice != "n" else False
    
    return username, mining_key, use_lower_diff


def connect_to_server(address, port):
    """Connect to the server and return the socket."""
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialize the socket object
    try:
        soc.connect((address, port))
        logging.info(f"Successfully connected to {address}:{port}")
        return soc
    except Exception as e:
        logging.error(f"Failed to connect to {address}:{port}, Error: {e}")
        return None


def calculate_hash(job_data, difficulty):
    """Perform the hashing work for the mining job."""
    base_hash = hashlib.sha1(str(job_data[0]).encode('ascii'))
    for result in range(100 * int(difficulty) + 1):
        temp_hash = base_hash.copy()
        temp_hash.update(str(result).encode('ascii'))
        ducos1 = temp_hash.hexdigest()
        if job_data[1] == ducos1:
            return result, time.time()
    return None, None


def main():
    """Main mining loop."""
    global accepted_shares, rejected_shares

    username, mining_key, use_lower_diff = get_user_input()

    # Use default address and port directly
    node_address = DEFAULT_NODE_ADDRESS
    node_port = DEFAULT_NODE_PORT

    while True:
        try:
            logging.info("Searching for fastest connection to the server...")

            # Attempt to connect to the server
            soc = connect_to_server(node_address, node_port)
            if not soc:
                continue  # Retry connection if failed

            server_version = soc.recv(100).decode()
            logging.info(f"Server Version: {server_version}")

            # Mining section
            while True:
                difficulty_level = "LOW" if use_lower_diff else "MEDIUM"
                soc.send(bytes(f"JOB,{username},{difficulty_level},{mining_key}", encoding="utf8"))

                # Receive job
                job = soc.recv(1024).decode().rstrip("\n").split(",")
                
                job_hash, difficulty = job[1], job[2]
                
                # Perform hashing and calculate result
                hashing_start_time = time.time()
                result, hashing_end_time = calculate_hash(job, difficulty)
                
                if result is not None and hashing_end_time:
                    hashrate = result / (hashing_end_time - hashing_start_time)
                    soc.send(bytes(f"{result},{hashrate},cppDuco_v1", encoding="utf8"))

                    feedback = soc.recv(1024).decode().rstrip("\n")
                    if feedback == "GOOD":
                        accepted_shares += 1  # Increment accepted shares counter
                        # Log accepted share in green with "A:"
                        console.log(f"[green]A: Accepted share: {result} Hashrate: {int(hashrate / 1000)} kH/s Difficulty: {difficulty}[/green]")
                    else:
                        rejected_shares += 1  # Increment rejected shares counter
                        # Log rejected share in red with "R:"
                        console.log(f"[red]R: Rejected share: {result} Hashrate: {int(hashrate / 1000)} kH/s Difficulty: {difficulty}[/red]")

                    # Display the accept/reject ratio
                    console.log(f"[yellow]Accept/Reject Ratio: {accepted_shares}/{accepted_shares + rejected_shares}[/yellow]")

        except Exception as e:
            logging.error(f"Error occurred: {e}, restarting in 5 seconds.")
            time.sleep(5)  # Ensure correct indentation for sleep

            os.execl(sys.executable, sys.executable, *sys.argv)  # Restart the script

if __name__ == "__main__":
    main()
                        
