import pytest
from replenishment import ReplenishmentInput, suggested_qty


def test_rule_is_deterministic():
    item=ReplenishmentInput('COFFEE-250',10,2,3)
    assert suggested_qty(item)==5
    assert suggested_qty(item)==5


def test_open_purchase_can_remove_replenishment_need():
    assert suggested_qty(ReplenishmentInput('BEANS',10,8,5))==0


@pytest.mark.parametrize('values',[(10,-1,0),(10,0,-1),(10,True,0)])
def test_invalid_quantities_are_rejected(values):
    with pytest.raises(ValueError):
        suggested_qty(ReplenishmentInput('BAD',*values))
