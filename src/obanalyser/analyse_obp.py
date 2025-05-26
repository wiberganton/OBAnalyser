import obplib as obp

from src.obanalyser.data_classes import FileStats

def analyse_obp_files(obp_files):
    data = []
    for file in obp_files:
        data.append(analyse_obp_file(file))
    return data

def analyse_obp_file(obp_file):
    # input is (string with obp_path, number of repetitions)
    # returns an data_classes.FileStats object
    return analyse_obp_elements(obp.read_obp(obp_file[0]), nmb_repetitions=obp_file[1])

def analyse_obp_elements(obp_elements, nmb_repetitions=1):
    t = 0  # s
    energy = 0  # J
    nmb_spots = 0  # n
    line_length = 0  # um

    for element in obp_elements:
        if not isinstance(element, list):
            element = [element]
        for lst_el in element:
            if isinstance(lst_el, obp.TimedPoints):
                dwellTimes = fill_zeros_with_last_nonzero(lst_el.dwellTimes)
                energy += lst_el.bp.power * sum(dwellTimes) / 1e9
                nmb_spots += len(dwellTimes)
                t += sum(dwellTimes) / 1e9
            elif isinstance(lst_el, (obp.Line, obp.Curve)):
                t += lst_el.get_segment_duration()
                energy += lst_el.bp.power * lst_el.get_segment_duration()
                line_length += lst_el.get_segment_length()

    data = FileStats(
        time = t,
        energy = energy,
        nmb_spots = nmb_spots,
        line_length = line_length,
        nmb_repetitions = nmb_repetitions
    )
    return data

def fill_zeros_with_last_nonzero(data):
    # use for replacing zeroes in dwell time calculation
    result = []
    last_value = None
    for value in data:
        if value != 0:
            last_value = value
        result.append(last_value if last_value is not None else 0)
    return result