import pytest
from replenishment import ReplenishmentInput, ReplenishmentDraft, draft_is_current, suggested_qty


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


def test_draft_must_match_current_data_version_before_confirmation():
    item=ReplenishmentInput('COFFEE-250',10,2,3)
    draft=ReplenishmentDraft(item,'inventory-v1',suggested_qty(item))
    assert draft_is_current(draft,'inventory-v1') is True
    assert draft_is_current(draft,'inventory-v2') is False
    with pytest.raises(ValueError):
        draft_is_current(draft,'')
