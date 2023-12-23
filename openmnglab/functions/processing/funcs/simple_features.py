import sys
from math import log, e
from typing import Self

import pandas as pd
import numpy as np
import quantities as pq
from pandas import Series, DataFrame

from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.functions.base import FunctionBase
from openmnglab.functions.processing.funcs.interval_data import LEVEL_COLUMN
from openmnglab.util.pandas import index_names

import math
SPDF_FEATURES = tuple((f"F{i + 1}" for i in range(24)))


def mean_change_between(series: Series, high: float, low: float):
    return np.linalg.norm([high - low, series[high] - series[low]])


def slope_ratio(sequence, a, b, c):
    part_a = (sequence[b] - sequence[a]) * (c - b)
    part_b = (sequence[c] - sequence[b]) * (b - a)
    return part_a / part_b


def rms(sequence):
    return np.sqrt(sequence.dot(sequence) / sequence.size)


def iqr(sequence):
    Q3 = np.quantile(sequence, 0.75)
    Q1 = np.quantile(sequence, 0.25)
    return Q3 - Q1


def sampling_moment_dev(sequence, n) -> float:
    return pow(np.std(sequence), n)  # moment(sequence, n) / pow(np.dev(sequence), n)

def first_crossing(row):
    curr_negs = 0
    idx = 0
    for i, item in enumerate(row.values):
        if curr_negs > 4:
            return idx -4
        if item < 0:
            idx = i
            curr_negs+=1
        else:
            curr_negs = 0

    return idx


def min_first_half(row):
    c = int(len(row) / 2)
    return row[:c].idxmin()

def max_first_half(row):
    c = int(len(row) / 2)
    return row[:c].idxmax()

def min_sec_half(row):
    c = int(len(row) / 2)
    return row[c:].idxmin()

def max_sec_half(row):
    c = int(len(row) / 2)
    return row[c:].idxmax()

def min_max_height(row):
    c = int(len(row) / 2)
    return abs(int(row[:c].idxmax()) - int(row[:c].idxmin()))

def euclidean_distance(point1, point2):
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

# Calculate Euclidean distance between max and min points in the first half of the row
def euclid_distance_min_max(row):
    max_point = (row['max_first_half_idx'], row[row['max_first_half_idx']])
    min_point = (row['min_first_half_idx'], row[row['min_first_half_idx']])
    return euclidean_distance(max_point, min_point)

# Calculate Euclidean distance between max and min points in the second half of the row
def euclid_distance_min_max2(row):
    max_point = (row['max_sec_half_idx'], row[row['max_sec_half_idx']])
    min_point = (row['min_sec_half_idx'], row[row['min_sec_half_idx']])
    return euclidean_distance(max_point, min_point)

class SimpleFeaturesFunc(FunctionBase):
    def __init__(self, dtype=np.float64, mode="diff"):
        self.a: PandasContainer[DataFrame] = None
        self.series_b_container: PandasContainer[DataFrame] = None
        self.chosen_series = self.a

    def build_unitdict(self, df):
        units: dict[str, pq.Quantity] = dict()

        for c in df.columns:
            units[c] = pq.dimensionless #float
        
        for index_name in index_names(self.a.data.index):
            units[index_name] = self.a.units[index_name]
        units["idx"] = pq.dimensionless

        return units

    def execute(self) -> PandasContainer[DataFrame]:
        df_a = pd.DataFrame([self.a.data.values])
        #print(df_a)
        df_results = df_a.copy()
        df_results["min_first_half_idx"] = df_a.apply(min_first_half, axis=1)
        df_results["max_first_half_idx"] = df_a.apply(max_first_half, axis=1)
        df_results["min_sec_half_idx"] = df_a.apply(min_sec_half, axis=1)
        df_results["max_sec_half_idx"] = df_a.apply(max_sec_half, axis=1)
        df_results["first_crossing"] = df_a.apply(first_crossing, axis=1)
        df_results["height"] = df_a.apply(min_max_height, axis=1)
        #df_results[f"recovery_at_{recov_at_x}"] = df.apply(recovery_at_x, axis=1)
        df_results["ed_first_half"] = df_results.apply(euclid_distance_min_max, axis=1)
        df_results["ed_second_half"] = df_results.apply(euclid_distance_min_max2, axis=1)

        columns_to_keep = ["min_first_half_idx", "max_first_half_idx", "min_sec_half_idx", "max_sec_half_idx", "first_crossing", "height", "ed_first_half", "ed_second_half"]

        df_results = df_results[columns_to_keep]

        df_results.index.name = "idx"
        #Template tracking in/out, quantile outlier removal as an option?
        return PandasContainer(df_results, self.build_unitdict(df_results))

    def set_input(self, a: PandasContainer[DataFrame]) -> Self:
        self.a = a
        return self
