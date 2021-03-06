import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import pandas as pd
from scipy import spatial

__author__ = "swang"


def check_boxplot(input_dir):
    """
    Generate a boxplot for each trip to check its nearest distance in meters.
    :param input_dir:
    :return:
    """
    data_plot = defaultdict(list)
    with os.scandir(input_dir) as entries:
        for entry in entries:
            entry_name = entry.name
            if entry.is_file() and entry_name.endswith(".csv"):
                with open(input_dir + entry_name, "r", encoding='utf-8') as csv_in:
                    cr = csv.reader(csv_in)
                    next(cr, None)  # skip header
                    trip_id = entry_name.split("_")[0]
                    for row in cr:
                        data_plot[trip_id].append(float(row[-1]))
    plt.boxplot(data_plot.values(), labels=data_plot.keys(), showfliers=False)
    plt.show()
    df = pd.DataFrame(list(data_plot.values()))
    df.T.describe().to_csv("statistics_dist.csv")


def check_order(input_dir):
    """
    Check if the results are ordered in time.
    :param input_dir:
    :return:
    """
    with os.scandir(input_dir) as entries:
        for entry in entries:
            entry_name = entry.name
            if entry.is_file() and entry_name.endswith(".csv"):
                with open(input_dir + entry_name, "r", encoding='utf-8') as csv_in:
                    print("\n", entry_name)
                    cr = csv.reader(csv_in)
                    next(cr, None)  # skip header
                    time_prev = 0
                    pre_row = []
                    for row in cr:
                        time = float(row[-2])
                        if time < time_prev:
                            print("=== Outlier Founded ===")
                            print(pre_row)
                            print(row)
                        time_prev = time
                        pre_row = row


def load_def_trips(def_trips_dir):
    def_trips = defaultdict(list)
    with os.scandir(def_trips_dir) as entries:
        for entry in entries:
            entry_name = entry.name
            if entry.is_file() and entry_name.endswith(".csv"):
                with open(def_trips_dir + entry_name, "r", encoding='utf-8') as csv_in:
                    cr = csv.reader(csv_in)
                    next(cr, None)  # skip header
                    for row in cr:
                        if len(row[1]) > 1:  # select bus stops
                            def_trips[entry_name].append(row)
    return def_trips


def nearest_gps(gps_trips_dir, def_trips, gps_stop_trips_dir):
    with os.scandir(gps_trips_dir) as entries:
        for entry in entries:
            entry_name = entry.name
            if entry.is_file() and entry_name.endswith(".csv"):

                # 1 construct a kd-tree after iterating each gps_trip
                gps_trips = {}  # key: location
                locations = []
                with open(gps_trips_dir + entry_name, "r") as csv_in:
                    cr = csv.reader(csv_in)
                    next(cr, None)  # skip header
                    for i in cr:
                        time_stamp = int(i[0])
                        lon = i[1]
                        lat = i[2]
                        loc = (float(lat), float(lon))
                        locations.append(loc)
                        gps_trips[loc] = time_stamp
                kd_tree = spatial.cKDTree(locations)

                # 2 for each row in def_trip with bus stops only,
                # generate its corresponding information of its nearest point in gps_trip
                # gps_stop_trip = [["seq_id", "stop_name", "lon", "lat",
                #                   "arr_time", "aggregated_dist", "np_time", "np_dist", "agg_time"]]
                gps_stop_trip = [["aggregated_dist", "agg_time"]]
                def_trip_file = entry_name.split("_")[2]
                print("def_trip_file:", def_trip_file)
                for i in def_trips[def_trip_file]:
                    seq_id = i[0]
                    aggregated_dist = float(i[2])
                    lat = i[4]
                    lon = i[5]
                    query_point = (float(lat), float(lon))
                    _, ind = kd_tree.query(query_point)
                    nearest_point = locations[ind]
                    np_time = int(gps_trips[nearest_point] / 10e5)
                    if seq_id == "1":
                        start_time = np_time
                    agg_time = np_time - start_time
                    new_row = [aggregated_dist, agg_time]
                    gps_stop_trip.append(new_row)
                    del locations[:ind]  # re-construct kd-tree to ensure the timestamp is not decreasing
                    kd_tree = spatial.cKDTree(locations)
                global trip_id
                with open(gps_stop_trips_dir + str(trip_id) + "_" + str(start_time) + ".csv", "w",
                          encoding='utf-8') as csv_out:
                    cw = csv.writer(csv_out)
                    cw.writerows(gps_stop_trip)


def main():
    home_dir = "/Users/shenwang/Documents/datasets/dublin_bus/"
    bus_line_number = "145"
    gps_trips_dir = home_dir + "processed/gps_trips/" + bus_line_number + "/"
    def_trips_dir = home_dir + "processed/def_trips/" + bus_line_number + "/"
    gps_stop_trips_dir = home_dir + "processed/stop_trips/" + bus_line_number + "/"
    output_dir = home_dir + "plots/" + bus_line_number + "_stops/"
    if not os.path.exists(gps_stop_trips_dir):
        # create if not exist
        os.mkdir(gps_stop_trips_dir)
    if not os.path.exists(output_dir):
        # create if not exist
        os.mkdir(output_dir)
    # 1. load defined trips with bus stops only
    def_trips = load_def_trips(def_trips_dir)
    # check_order(gps_stop_trips_dir)
    # check_boxplot(gps_stop_trips_dir)
    count = 0
    for gps_trips_day_dir in os.listdir(gps_trips_dir):
        if len(gps_trips_day_dir) != 8:
            continue
        with os.scandir(gps_trips_dir + gps_trips_day_dir) as entry:
            count += len(list(entry))
        # 2. for each input gps_trip, output gps_stop_trip with the same file name
        nearest_gps(gps_trips_dir + gps_trips_day_dir + "/", def_trips, gps_stop_trips_dir)
    print("Total number of trips:", count)


if __name__ == '__main__':
    trip_id = 0
    main()
