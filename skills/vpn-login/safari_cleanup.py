import time
import subprocess

def close_safari_windows():
    applescript = '''
    tell application "Safari"
        close every window
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', applescript], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        pass

if __name__ == "__main__":
    print("🧹 Starting Safari Cleanup Watchdog (Interval: 10 mins)...", flush=True)
    while True:
        try:
            close_safari_windows()
        except:
            pass
        # Sleep for 10 minutes
        time.sleep(600)
