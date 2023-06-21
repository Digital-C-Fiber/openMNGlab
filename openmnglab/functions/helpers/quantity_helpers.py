import quantities as pq


def rescale_pq(base: pq.Quantity, *quant: pq.Quantity) -> tuple[pq.Quantity, ...]:
    base_u = base.units
    t = tuple(quantity.rescale(base_u) for quantity in quant)
    return t


def magnitudes(*quantities: pq.Quantity, unpack: bool = True) -> tuple:
    return tuple(np_val if not unpack or np_val.ndim > 0 else np_val.item() for np_val in (q.magnitude for q in quantities))
