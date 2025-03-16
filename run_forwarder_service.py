#!/usr/bin/env python3
"""
Run Telegram to SMS Forwarder as a Service
This script runs the Telegram to SMS forwarder as a background service.
"""

import os
import sys
import time
import logging
import subprocess
import signal
import atexit
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("forwarder_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Path to the forwarder script
FORWARDER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'start_forwarder.py')

# PID file to store the process ID
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'forwarder.pid')

# Flag to control the service
running = True

def write_pid(pid):
    """Write the process ID to the PID file."""
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))

def read_pid():
    """Read the process ID from the PID file."""
    try:
        with open(PID_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def is_process_running(pid):
    """Check if a process with the given ID is running."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def start_forwarder():
    """Start the forwarder process."""
    logger.info("Starting Telegram to SMS Forwarder service...")
    
    # Check if the forwarder is already running
    pid = read_pid()
    if pid and is_process_running(pid):
        logger.info(f"Forwarder is already running with PID {pid}")
        return pid
    
    # Start the forwarder process
    try:
        # Create log file for the forwarder output
        log_file = open("forwarder_output.log", "a")
        log_file.write(f"\n\n--- Starting forwarder at {datetime.now()} ---\n\n")
        log_file.flush()
        
        process = subprocess.Popen(
            [sys.executable, FORWARDER_SCRIPT],
            stdout=log_file,
            stderr=log_file,
            universal_newlines=True
        )
        
        # Write the process ID to the PID file
        write_pid(process.pid)
        
        logger.info(f"Forwarder started with PID {process.pid}")
        return process.pid
    except Exception as e:
        logger.error(f"Failed to start forwarder: {e}")
        if 'log_file' in locals():
            log_file.close()
        return None

def stop_forwarder():
    """Stop the forwarder process."""
    logger.info("Stopping Telegram to SMS Forwarder service...")
    
    # Read the process ID from the PID file
    pid = read_pid()
    if not pid:
        logger.info("No PID file found, forwarder is not running")
        return True
    
    # Check if the process is running
    if not is_process_running(pid):
        logger.info(f"Process with PID {pid} is not running")
        os.remove(PID_FILE)
        return True
    
    # Send SIGTERM to the process
    try:
        os.kill(pid, signal.SIGTERM)
        
        # Wait for the process to terminate
        for _ in range(10):
            if not is_process_running(pid):
                logger.info(f"Process with PID {pid} terminated")
                os.remove(PID_FILE)
                return True
            time.sleep(1)
        
        # If the process is still running, send SIGKILL
        logger.warning(f"Process with PID {pid} did not terminate, sending SIGKILL")
        os.kill(pid, signal.SIGKILL)
        
        # Wait for the process to terminate
        for _ in range(5):
            if not is_process_running(pid):
                logger.info(f"Process with PID {pid} terminated")
                os.remove(PID_FILE)
                return True
            time.sleep(1)
        
        logger.error(f"Failed to terminate process with PID {pid}")
        return False
    except OSError as e:
        logger.error(f"Error stopping forwarder: {e}")
        return False

def restart_forwarder():
    """Restart the forwarder process."""
    logger.info("Restarting Telegram to SMS Forwarder service...")
    
    # Stop the forwarder
    stop_forwarder()
    
    # Wait a moment
    time.sleep(2)
    
    # Start the forwarder
    return start_forwarder()

def cleanup():
    """Clean up resources when the service exits."""
    global running
    running = False
    stop_forwarder()

def signal_handler(sig, frame):
    """Handle signals to gracefully stop the service."""
    global running
    logger.info(f"Received signal {sig}, stopping service...")
    running = False
    sys.exit(0)

def run_service():
    """Run the forwarder service."""
    global running
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function
    atexit.register(cleanup)
    
    # Start the forwarder
    pid = start_forwarder()
    if not pid:
        logger.error("Failed to start forwarder")
        return
    
    # Monitor the forwarder process
    while running:
        try:
            # Check if the forwarder is still running
            if not is_process_running(pid):
                logger.warning("Forwarder process has stopped, restarting...")
                pid = start_forwarder()
                if not pid:
                    logger.error("Failed to restart forwarder")
                    time.sleep(60)  # Wait a minute before trying again
            
            # Wait a bit before checking again
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping service...")
            running = False
            break
        except Exception as e:
            logger.error(f"Error monitoring forwarder: {e}")
            time.sleep(60)  # Wait a minute before trying again

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            start_forwarder()
        elif command == 'stop':
            stop_forwarder()
        elif command == 'restart':
            restart_forwarder()
        elif command == 'status':
            pid = read_pid()
            if pid and is_process_running(pid):
                print(f"Forwarder is running with PID {pid}")
            else:
                print("Forwarder is not running")
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_forwarder_service.py [start|stop|restart|status]")
    else:
        # Run the service
        run_service() 