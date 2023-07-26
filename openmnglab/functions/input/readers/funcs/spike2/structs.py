from typing import Any

import numpy as np

from openmnglab.functions.input.readers.funcs.spike2.hdfmat import HDFMatGroup


class _Spike2Base:

    def __init__(self, hdfgroup: HDFMatGroup):
        self._hdfgroup = hdfgroup

    @property
    def hdfgroup(self) -> HDFMatGroup:
        return self._hdfgroup


class _TitleMixin(_Spike2Base):
    _title = None

    @property
    def title(self) -> str:
        if self._title is None:
            title_tuple = self.hdfgroup['title']
            self._title = title_tuple[0] if len(title_tuple) > 0 else ""
        return self._title


class _CommentMixin(_Spike2Base):
    _comment = None

    @property
    def comment(self) -> str:
        if self._comment is None:
            comment_tuple = self.hdfgroup['comment']
            self._comment = comment_tuple[0] if len(comment_tuple) > 0 else ""
        return self._comment


class _LengthMixin(_Spike2Base):
    _length = None

    @property
    def length(self) -> int:
        if self._length is None:
            val = self.hdfgroup['length'].astype(np.uint64)
            self._length = val.item()
        return self._length


class _LevelMixin(_Spike2Base):
    _level = None

    @property
    def level(self) -> np.ndarray:
        if self._level is None:
            val = self.hdfgroup['level']
            self._level = val.astype(np.int8).flatten()
        return self._level


class _TimesMixin(_Spike2Base):
    _times = None

    @property
    def times(self):
        if self._times is None:
            val = self.hdfgroup['times']
            self._times = val.flatten()
        return self._times


class _TextMixin(_Spike2Base):
    _text = None

    @property
    def text(self):
        if self._text is None:
            val = self.hdfgroup['text']
            self._text = val
        return self._text


class _CodesMixin(_Spike2Base):
    _codes = None

    @property
    def codes(self):
        if self._codes is None:
            val = self.hdfgroup['codes']
            self._codes = val
        return self._codes


class _StartMixin(_Spike2Base):
    _start = None

    @property
    def start(self):
        if self._start is None:
            val = self.hdfgroup['start']
            self._start = val.flatten()[0]
        return self._start


class _IntervalMixin(_Spike2Base):
    _interval = None

    @property
    def interval(self):
        if self._interval is None:
            val = self.hdfgroup['interval']
            self._interval = val.flatten()[0]
        return self._interval


class _ValuesMixin(_Spike2Base):
    _values = None

    @property
    def values(self):
        if self._values is None:
            val = self.hdfgroup['values']
            self._values = val.flatten()
        return self._values


class Spike2UnbinnedEvent(_LengthMixin, _TitleMixin, _LevelMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2BinnedEvent(_LengthMixin, _ValuesMixin, _TitleMixin, _StartMixin, _TimesMixin, _IntervalMixin, _Spike2Base):
    ...


class Spike2TimeView(_StartMixin, _Spike2Base):
    ...


class Spike2Marker(_LengthMixin, _TitleMixin, _CodesMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Realmark(_LengthMixin, _ValuesMixin, _TitleMixin, _CodesMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Result(_LengthMixin, _ValuesMixin, _TitleMixin, _StartMixin, _TimesMixin, _IntervalMixin, _Spike2Base):
    ...


class Spike2Textmark(_LengthMixin, _TitleMixin, _CodesMixin, _TimesMixin, _TextMixin, _Spike2Base):
    ...


class Spike2Realwave(_LengthMixin, _ValuesMixin, _TitleMixin, _StartMixin, _IntervalMixin, _Spike2Base):
    ...


class Spike2Waveform(_LengthMixin, _ValuesMixin, _TitleMixin, _StartMixin, _IntervalMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Waveform(_LengthMixin, _ValuesMixin, _TitleMixin, _StartMixin, _IntervalMixin, _TimesMixin, _Spike2Base):
    ...


class Spike2Wavemark(_LengthMixin, _ValuesMixin, _TitleMixin, _TimesMixin, _CodesMixin, _IntervalMixin, _Spike2Base):
    ...


class Spike2XYData(_LengthMixin, _TitleMixin, _Spike2Base):
    ...


_id_order: list[dict[Any, tuple[set[str],set[str]]]] = [{Spike2UnbinnedEvent: ({'level'}, set()), Spike2TimeView: ({'name'}, {'length', 'title'}),
             Spike2Textmark: ({'text'}, set()), Spike2Wavemark: ({'traces', 'trigger'}, set()),
             Spike2XYData: ({'xvalues', 'yvalues'}, set()), },
            {Spike2Realwave: (set(), {'times'}), Spike2Result: ({'xunits'}, {'comment'}),
             Spike2Marker: ({'resolution'}, {'values'}), Spike2Realmark: ({'items'}, set()), },
            {Spike2Waveform: ({'offset', 'scale', 'units'}, set()), }, {Spike2BinnedEvent: (
    {'times', 'title', 'comment', 'interval', 'values', 'length', 'start'},
    {'offset', 'level', 'text', 'yvalues', 'xunits', 'scale', 'items', 'name', 'trigger', 'xvalues', 'traces',
     'resolution', 'codes', 'units'}), }, {}, ]


def spike2_struct(group: HDFMatGroup) -> Any:
    for round in _id_order:
        for cls, (included_fields, excluded_files) in round.items():
            key_set = set(group.keys())
            if included_fields.issubset(key_set) and excluded_files.isdisjoint(key_set):
                return cls(group)
    raise Exception("Could not identify struct")
