import subprocess
import time
import sys
import socket

def is_port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def kill_process_on_port(port):
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            check=True
        )
        
        killed = False
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        subprocess.run(
                            ['taskkill', '/F', '/PID', pid],
                            capture_output=True,
                            check=True
                        )
                        print(f"Killed process {pid} on port {port}")
                        killed = True
                    except subprocess.CalledProcessError:
                        print(f"Failed to kill process {pid}")
        
        if killed:
            time.sleep(1)
        return killed
    except Exception as e:
        print(f"Error killing process: {e}")
        return False

def main():
    port = 3000
    
    if is_port_in_use(port):
        print(f"Port {port} is already in use")
        if kill_process_on_port(port):
            print(f"Process on port {port} has been killed")
        else:
            print(f"Failed to kill process on port {port}")
            sys.exit(1)
    
    if is_port_in_use(port):
        print(f"Port {port} is still in use")
        sys.exit(1)
    
    print(f"Port {port} is free, you can start the server now")

if __name__ == '__main__':
    main()
