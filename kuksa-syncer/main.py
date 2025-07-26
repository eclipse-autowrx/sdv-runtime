
import json
import time
import threading
import sys

# Global variable monitoring
_monitored_vars = ['a']
_monitoring_active = True

def _monitor_globals():
    while _monitoring_active:
        try:
            globals_data = {}
            for var_name in _monitored_vars:
                if var_name in globals():
                    value = globals()[var_name]
                    try:
                        # Try to serialize the value
                        if isinstance(value, (int, float, str, bool, list, dict, tuple)):
                            globals_data[var_name] = value
                        else:
                            globals_data[var_name] = str(type(value).__name__) + ': ' + str(value)[:100]
                    except:
                        globals_data[var_name] = str(type(value).__name__)
                else:
                    globals_data[var_name] = "undefined"
            
            # Print in a format that can be captured by pexpect
            print(f"GLOBALS_UPDATE: {json.dumps(globals_data)}", flush=True)
        except Exception as e:
            print(f"GLOBALS_ERROR: {str(e)}", flush=True)
        
        time.sleep(1)  # Update every second

# Start monitoring in a separate thread
_monitor_thread = threading.Thread(target=_monitor_globals, daemon=True)
_monitor_thread.start()

# Function to stop monitoring
def stop_global_monitoring():
    global _monitoring_active
    _monitoring_active = False

import time

# Global variable 'a'
a = 0

def main():
    """
    Main function to loop from 0 to 100, print the index,
    update a global variable, and sleep for 1 second.
    """
    global a # Declare 'a' as global to modify it inside the function

    print("Starting the loop...")
    for i in range(101): # Loop from 0 to 100 (range(101) goes up to 100)
        a = i # Set the global variable 'a' to the current index
        print(f"Current index: {i}, Global variable 'a': {a}")
        time.sleep(1) # Sleep for 1 second

    print("Loop finished.")

if __name__ == "__main__":
    main()
