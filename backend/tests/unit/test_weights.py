from app.domain.enums import Role
from app.supervisor.accuracy import AccuracyTracker


def test_agent_weights_chosen_vs_related():
    """Role-based multiplier test: chosen market gets a higher base weight than related markets."""
    tracker = AccuracyTracker()
    weight_chosen = tracker.get_weight("GOLD", Role.CHOSEN)
    weight_related = tracker.get_weight("GOLD", Role.RELATED)
    assert weight_chosen > weight_related


def test_weights_change_dynamically_after_correct_and_wrong_calls():
    """
    Dynamic accuracy test: weights must adapt over several days.
    Consecutive wrong calls must lower weight, consecutive correct calls must raise weight.
    """
    tracker = AccuracyTracker()
    initial_weight = tracker.get_weight("CRYPTO", Role.RELATED)
    initial_acc = tracker.get_accuracy("CRYPTO")

    # Simulate 5 consecutive losing / wrong prediction days
    for _ in range(5):
        tracker.record_prediction("CRYPTO", was_correct=False)

    wrong_streak_acc = tracker.get_accuracy("CRYPTO")
    wrong_streak_weight = tracker.get_weight("CRYPTO", Role.RELATED)

    assert wrong_streak_acc < initial_acc, "Accuracy should decline after wrong calls"
    assert wrong_streak_weight < initial_weight, "Weight should decrease after wrong calls"

    # Now simulate 7 consecutive winning / correct prediction days
    for _ in range(7):
        tracker.record_prediction("CRYPTO", was_correct=True)

    correct_streak_acc = tracker.get_accuracy("CRYPTO")
    correct_streak_weight = tracker.get_weight("CRYPTO", Role.RELATED)

    assert correct_streak_acc > wrong_streak_acc, "Accuracy should recover after correct calls"
    assert correct_streak_weight > wrong_streak_weight, "Weight should increase after correct calls"
