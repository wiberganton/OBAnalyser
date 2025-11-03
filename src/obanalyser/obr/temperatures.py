import json
import pandas as pd

def read_mqqt(log_file, tag, t0, value_key='Temperature', time_key='time'):
    # File paths

    # List to collect the extracted data
    data = []
    # Read and extract temperature/time
    with open(log_file, 'r') as f:
        for line in f:
            if line.split(" ", 1)[0] == tag:
                try:
                    json_part = line.split(' ', 1)[1]
                    values = json.loads(json_part)
                    #print(values)
                    temperature = values.get(value_key)
                    time = int(values.get(time_key))  # Make sure it's an int
                    if time > t0:
                        current_time = (time - t0)/1e9
                        data.append([current_time, temperature])
                except (IndexError, json.JSONDecodeError, TypeError, ValueError):
                    continue  # skip malformed lines

    # Normalize time: convert nanoseconds to seconds and set first to 0
    last_part = tag.split("/")[-1]
    df = pd.DataFrame(data, columns=['Time (s)', last_part])
    return df