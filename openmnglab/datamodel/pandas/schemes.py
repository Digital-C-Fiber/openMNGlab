from pandera import Column, Index, DataFrameSchema, SeriesSchema, MultiIndex

from openmnglab.datamodel.pandas.model import PandasDataScheme

TRACK = "track"
SPIKE_TS = "spike_ts"
SPIKE_IDX = "spike_idx"
STIM_IDX = "stim_idx"
STIM_TS = "stim_ts"
STIM_LBL = "stim_label"
RESP_IDX = "resp_idx"
TRACK_SPIKE_IDX = "track_spike_idx"
TIMESTAMP = "timestamp"
CONT_REC = "continuous recording"


def time_waveform() -> PandasDataScheme[SeriesSchema]:
    return PandasDataScheme(SeriesSchema(float, index=Index(float)))


def int_list() -> PandasDataScheme[SeriesSchema]:
    return PandasDataScheme(SeriesSchema(int, index=Index(int)))


def float_list() -> PandasDataScheme[SeriesSchema]:
    return PandasDataScheme(SeriesSchema(float, index=Index(float)))


def str_float_list() -> PandasDataScheme[SeriesSchema]:
    return PandasDataScheme(SeriesSchema(str, index=Index(float)))


def related_spikes() -> PandasDataScheme[DataFrameSchema]:
    return PandasDataScheme(DataFrameSchema({
        SPIKE_TS: Column(float),
        STIM_IDX: Column(int)
    },
        index=Index(int, name=SPIKE_IDX),
        name="related spikes"))


def sorted_spikes() -> PandasDataScheme[DataFrameSchema]:
    return PandasDataScheme(DataFrameSchema({
        SPIKE_TS: Column(float),
    },
        index=MultiIndex(indexes=[Index(str, name=TRACK), Index(int, name=TRACK_SPIKE_IDX)]),
        name="sorted spikes"))

