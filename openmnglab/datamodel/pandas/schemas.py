from pandera import Column, Index, DataFrameSchema, SeriesSchema, MultiIndex, Category

from openmnglab.datamodel.pandas.model import PandasDataSchema

TRACK = "track"
SPIKE_TS = "spike timestamp"
STIM_IDX = "stimulus index"
STIM_TS = "stimulus timestamp"
TRACK_SPIKE_IDX = "track_spike_idx"
TIMESTAMP = "timestamp"
SIGNAL = "signal"
TEMPERATURE = "temperature"
MASS = "mass"
STIM_TYPE = "stimulus type"
COMMENT = "comment"


def float_timeseries(name: str, index_name: str = TIMESTAMP) -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(float, index=Index(float, name=index_name), name=name))


def str_eventseries(name: str, index_name: str = TIMESTAMP) -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(str, index=Index(float, name=index_name), name=name))


def stimulus_list() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(float, index=MultiIndex(
        indexes=[Index(int, name=STIM_IDX), Index(Category, name=STIM_TYPE)]),
                                         name=STIM_TS))


def sorted_spikes() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(float,
                                         index=MultiIndex(
                                             indexes=[Index(int, name=STIM_IDX), Index(str, name=TRACK),
                                                      Index(int, name=TRACK_SPIKE_IDX)]),
                                         name=SPIKE_TS))
