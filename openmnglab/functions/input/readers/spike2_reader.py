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
    """ Load data from Spike2 recordings exported to MATLAB v7.3+ files
        Attempts to load data from 9 channels. To avoid loading data from a channel, pass ``None`` as a channels name,to avoid loading data from itl.
        Channels can be specified either by their name or their numeric channel id. Channel ids are only available, if the MATLAB file
        was exported without the "Use source channel name in variable names" option, as they can only be loaded from the MATLAB structure name.
        Channel names are loaded from the respective attribute of the matlab structure and not from its name.

        Use the ``start`` and ``end`` parameters to load only a section of the data by specifying the start, respective end timestamps in seconds.

        You can provide a quantity for all channels which require one.

        :param path: Path to the file
        :param signal: Name or channel id of the signal channel. Pass ``None`` to avoid loading it. Defaults to "Signal".
        :param temp: Name or channel id of the temperature channel. Pass ``None`` to avoid loading it. Defaults to "Temp".
        :param mass: Name or channel id of the mass / force channel. Pass ``None`` to avoid loading it. Defaults to "Force".
        :param v_chan: Name or channel id of the v chan channel. Pass ``None`` to avoid loading it. Defaults to "V".
        :param ext_pul: Name or channel id of the external pulses channel. Pass ``None`` to avoid loading it. Defaults to 10.
        :param comments: Name or channel id of the comments channel. Pass ``None`` to avoid loading it. Defaults to 30.
        :param keyboard: Name or channel id of the keyboard channel. Pass ``None`` to avoid loading it. Defaults to 31.
        :param digmark: Name or channel id of the digmark channel. Pass ``None`` to avoid loading it. Defaults to 32.
        :param wavemarks: Name or channel id of the wavemarks channel. Pass ``None`` to avoid loading it. Defaults to "nw-1".
        :param start: first timestamp to load from the file, defaults to 0
        :param end: last timestamp to load from the file, defaults to infinity
        :param mass_unit: Unit to use for the mass channel, defaults to gramms.
        :param signal_unit: Unit to use for the signal channel, defaults to microvolt
        :param temp_unit: Unit to use for the temperature channel, defaults to degree Celsius.
        :param v_chan_unit: Unit to use for the v_chan channel, defaults to dimensionless.
        :param time_unit: Unit to use for all timestamps, defaults to seconds.
    """

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
