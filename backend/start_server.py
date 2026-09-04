import subprocess
import time
import sys
import os
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
                        time.sleep(1)
                    except subprocess.CalledProcessError:
                        print(f"Failed to kill process {pid}")
    except Exception as e:
        print(f"Error killing process: {e}")

def wait_for_port_free(port, timeout=60):
    print(f"Waiting for port {port} to be free...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if not is_port_in_use(port):
            print(f"Port {port} is now free")
            return True
        print(f"Port {port} is still in use, waiting...")
        time.sleep(2)
    
    print(f"Timeout waiting for port {port} to be free")
    return False

def main():
    port = 3000
    
    if is_port_in_use(port):
        print(f"Port {port} is already in use")
        print("Do you want to kill the process using the port? (y/n)")
        response = input().strip().lower()
        
        if response == 'y':
            kill_process_on_port(port)
            if not wait_for_port_free(port):
                print("Failed to free the port")
                sys.exit(1)
        else:
            if not wait_for_port_free(port):
                print("Port is still in use, exiting")
                sys.exit(1)
    
    print("Starting server...")
    
    os.environ['WEBUI_SECRET_KEY'] = 'test-secret-key'
    os.environ['ENABLE_LITELLM'] = 'false'
    
    try:
        process = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'open_webui.main:app',
             '--host', '0.0.0.0', '--port', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"Server started with PID {process.pid}")
        print("Press Ctrl+C to stop the server")
        
        for line in process.stdout:
            print(line, end='')
            
    except KeyboardInterrupt:
        print("\nStopping server...")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("Server stopped")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
