import json
import pandas as pd

def get_exposure_times(log_file, t0):
    data = []
    seen_layers = set()  # to track already recorded layers
    # Read and extract temperature/time
    with open(log_file, 'r') as f:
        for line in f:
            # Skip any line that contains "Retry"
            if "Retry" in line:
                continue
            if 'freemelt/0/BuildProcess/0/BuildStatus/Trace/Activity' in line:
                try:
                    json_part = line.split(' ', 1)[1]
                    values = json.loads(json_part)
                    temperature = values.get('current_activity')
                    if temperature and temperature.startswith("Exposing OBP files"):
                        parts = temperature.split("layer")
                        if len(parts) > 1:
                            layer_number = parts[1].strip(" .")
                            # Skip if layer was already seen
                            if layer_number in seen_layers:
                                continue
                            seen_layers.add(layer_number)
                            time_ns = int(values.get('time'))  # Make sure it's an int
                            time = time_ns / 1e9
                            time -= t0  # Convert to seconds
                            if time > 0:
                                data.append([time, layer_number])
                except (IndexError, json.JSONDecodeError, TypeError, ValueError):
                    continue  # skip malformed lines
    df = pd.DataFrame(data, columns=['Time (s)', 'Exposure Layer'])
    # Optional: sort by layer number
    df['Exposure Layer'] = df['Exposure Layer'].astype(int)
    df = df.sort_values('Exposure Layer').reset_index(drop=True)
    return df

def get_power_times(log_file, t0):
    data = []
    with open(log_file, 'r') as f:
        for line in f:
            if 'freemelt/0/ElectronService/0/HighVoltageGenerator/Type/Current' in line:
                #print(line)
                try:
                    json_part = line.split(' ', 1)[1]
                    values = json.loads(json_part)
                    temperature = values.get('CurrentDemand')
                    time_ns = int(values.get('time'))  # Make sure it's an int
                    if time_ns > t0:
                        current_time = (time_ns - t0)/1e9
                        data.append([current_time, int(temperature*60)])
                except (IndexError, json.JSONDecodeError, TypeError, ValueError):
                    continue  # skip malformed lines
    df = pd.DataFrame(data, columns=['Time (s)', 'Power (W)'])
    return df