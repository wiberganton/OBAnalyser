import pandas as pd
import json

def get_layer_heights(log_file, t0=0):
    # List to collect the extracted data
    data = []
    z0 = None
    with open(log_file, 'r') as f:
        for line in f:
            if 'freemelt/0/RecoaterService/0/Recoater/Position/BuildServo' in line:
                try:
                    json_part = line.split(' ', 1)[1]
                    values = json.loads(json_part)

                    height = round(values.get('Location'), 3)
                    if z0 is None:
                        z0 = height
                        height = 0
                    else:
                        height = z0-height
                    time = int(values.get('time'))
                    if time >= t0:
                        data.append([height, (time-t0)/1e9])
                except (IndexError, json.JSONDecodeError, TypeError, ValueError):
                    continue  # skip malformed lines


    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['Build height (mm)', 'time'])
    df_unique = df.drop_duplicates(subset="Build height (mm)", keep="first").reset_index(drop=True)

    return df_unique