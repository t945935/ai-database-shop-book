from dataclasses import dataclass


@dataclass(frozen=True)
class ReplenishmentInput:
    sku: str
    target_stock: int
    available: int
    open_purchase_qty: int


def suggested_qty(item: ReplenishmentInput) -> int:
    for value in (item.target_stock, item.available, item.open_purchase_qty):
        if type(value) is not int or value < 0:
            raise ValueError('quantities must be non-negative integers')
    return max(0, item.target_stock - item.available - item.open_purchase_qty)
