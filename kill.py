import subprocess

def kill_python_processes():
    try:
        # Run 'tasklist' and filter for python.exe
        output = subprocess.check_output("tasklist | findstr python", shell=True, text=True)
        lines = output.strip().split("\n")

        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                pid = parts[1]
                print(f"Killing python process with PID {pid}...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True)
        print("✅ All Python processes terminated.")
    except subprocess.CalledProcessError:
        print("No Python processes running.")

kill_python_processes()
