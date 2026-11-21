from app.domain.enums import Role
from app.supervisor.accuracy import AccuracyTracker


def test_agent_weights_chosen_vs_related():
    tracker = AccuracyTracker()
    weight_chosen = tracker.get_weight("GOLD", Role.CHOSEN)
    weight_related = tracker.get_weight("GOLD", Role.RELATED)
    assert weight_chosen > weight_related
