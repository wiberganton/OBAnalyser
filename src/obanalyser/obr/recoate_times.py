import pandas as pd
import json

def get_recoate_times(log_file):
    # List to collect the extracted data
    data = []
    with open(log_file, 'r') as f:
        for line in f:
            if 'freemelt/0/BuildProcess/0/BuildStatus/Trace/Activity' in line:
                try:
                    json_part = line.split(' ', 1)[1]
                    values = json.loads(json_part)

                    temperature = values.get('current_activity')
                    if temperature.startswith("Recoat cycle"):
                        parts = temperature.split("Layer")
                        if len(parts) > 1:
                            layer_number = parts[1].strip()
                            time_ns = int(values.get('time'))  # Make sure it's an int
                            data.append([time_ns, int(layer_number)-1])
                except (IndexError, json.JSONDecodeError, TypeError, ValueError):
                    continue  # skip malformed lines


    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['Time (s)', 'Layer'])

    return df