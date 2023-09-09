from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd
import quantities as pq
from pandera import SeriesSchema, Index, MultiIndex, Category

from openmnglab.datamodel.pandas.model import PandasStaticDataScheme
from openmnglab.datamodel.pandas.schemes import TIMESTAMP, SIGNAL, MASS, TEMPERATURE
from openmnglab.functions.base import SourceFunctionDefinitionBase
from openmnglab.functions.input.readers.funcs.spike2_reader import SPIKE2_CHANID, Spike2ReaderFunc, SPIKE2_V_CHAN, \
    SPIKE2_LEVEL, SPIKE2_CODES, SPIKE2_DIGMARK, SPIKE2_KEYBOARD
from openmnglab.model.datamodel.interface import IOutputDataScheme
from openmnglab.model.planning.interface import IProxyData
from openmnglab.util.hashing import Hash


class Spike2Reader(SourceFunctionDefinitionBase[tuple[
    IProxyData[pd.Series], IProxyData[pd.Series], IProxyData[pd.Series], IProxyData[pd.Series], IProxyData[
        pd.Series]]]):

    def __init__(self, path: str | Path,
                 signal: SPIKE2_CHANID | None = "Signal",
                 temp: SPIKE2_CHANID | None = "Temp",
                 mass: SPIKE2_CHANID | None = "Force",
                 v_chan: SPIKE2_CHANID | None = "V",
                 ext_pul: SPIKE2_CHANID | None = 10,
                 comments: SPIKE2_CHANID | None = 30,
                 keyboard: SPIKE2_CHANID | None = 31,
                 digmark: SPIKE2_CHANID | None = 32,
                 wavemarks: SPIKE2_CHANID | None | Iterable[int | str] = "nw-1",
                 start: float = 0,
                 end: float = np.inf,
                 mass_unit: pq.Quantity = pq.g,
                 signal_unit: pq.Quantity = pq.microvolt,
                 temp_unit: pq.Quantity = pq.celsius,
                 v_chan_unit: pq.Quantity = pq.dimensionless,
                 time_unit: pq.Quantity = pq.second):
        super().__init__("codingchipmunk.spike2loader")
        self._start = start
        self._end = end
        self._signal_chan = signal
        self._temp_chan = temp
        self._mass = mass
        self._v_chan = v_chan
        self._ext_pul = ext_pul
        self._comments = comments
        self._keyboard = keyboard
        self._digmark = digmark
        self._wavemarks = wavemarks
        self._mass_unit = mass_unit
        self._signal_unit = signal_unit
        self._temp_unit = temp_unit
        self._v_chan_unit = v_chan_unit
        self._time_unit = time_unit
        self._path = path

    @property
    def config_hash(self) -> bytes:
        return Hash().dynamic(self._start) \
            .dynamic(self._end) \
            .dynamic(self._temp_chan) \
            .dynamic(self._signal_chan) \
            .dynamic(self._mass) \
            .dynamic(self._v_chan) \
            .dynamic(self._ext_pul) \
            .dynamic(self._comments) \
            .dynamic(self._keyboard) \
            .dynamic(self._digmark) \
            .quantity(self._mass_unit) \
            .quantity(self._signal_unit) \
            .quantity(self._temp_unit) \
            .quantity(self._v_chan_unit) \
            .quantity(self._time_unit) \
            .path(self._path) \
            .digest()

    @property
    def produces(self) -> Optional[Sequence[IOutputDataScheme] | IOutputDataScheme]:
        return PandasStaticDataScheme(SeriesSchema(float, index=Index(float, name=TIMESTAMP), name=SIGNAL)), \
            PandasStaticDataScheme(SeriesSchema(float, index=Index(float, name=TIMESTAMP), name=MASS)), \
            PandasStaticDataScheme(SeriesSchema(float, index=Index(float, name=TIMESTAMP), name=TEMPERATURE)), \
            PandasStaticDataScheme(SeriesSchema(float, index=Index(float, name=TIMESTAMP), name=SPIKE2_V_CHAN)), \
            PandasStaticDataScheme(SeriesSchema(np.int8, index=Index(float, name=TIMESTAMP), name=SPIKE2_LEVEL)), \
            PandasStaticDataScheme(SeriesSchema(str, index=MultiIndex(
                indexes=[Index(float, name=TIMESTAMP), Index(np.uint32, name=SPIKE2_CODES)]))), \
            PandasStaticDataScheme(SeriesSchema(Category, index=(Index(float, name=TIMESTAMP)), name=SPIKE2_DIGMARK)), \
            PandasStaticDataScheme(SeriesSchema(Category, index=(Index(float, name=TIMESTAMP)), name=SPIKE2_KEYBOARD))

    def new_function(self) -> Spike2ReaderFunc:
        return Spike2ReaderFunc(start=self._start,
                                end=self._end,
                                signal=self._signal_chan,
                                temp=self._temp_chan,
                                mass=self._mass,
                                v_chan=self._v_chan,
                                ext_pul=self._ext_pul,
                                comments=self._comments,
                                keyboard=self._keyboard,
                                digmark=self._digmark,
                                wavemarks=self._wavemarks,
                                mass_unit=self._mass_unit,
                                signal_unit=self._signal_unit,
                                temp_unit=self._temp_unit,
                                v_chan_unit=self._v_chan_unit,
                                time_unit=self._time_unit,
                                path=self._path)
