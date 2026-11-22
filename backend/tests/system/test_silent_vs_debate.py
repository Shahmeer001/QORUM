import pytest
from app.domain.enums import Mode, MsgType
from app.domain.models import SessionConfig
from app.services.session_service import SessionService


@pytest.mark.parametrize("scenario", ["bull", "bear", "neutral"])
def test_silent_vs_debate_differ_across_multiple_scenarios(scenario: str):
    """
    Evaluates that Silent mode and Debate mode differ systematically across multiple scenarios.
    Debate mode must engage in multi-round deliberation with final consensus synthesis,
    resulting in debate turns used and richer board dialogue than silent mode.
    """
    service = SessionService(db=None)
    cfg_silent = SessionConfig(
        mode=Mode.SILENT, target="GOLD", asset="XAUUSD", scenario=scenario
    )
    cfg_debate = SessionConfig(
        mode=Mode.DEBATE, target="GOLD", asset="XAUUSD", scenario=scenario
    )

    res_silent = service.run_session(cfg_silent)
    res_debate = service.run_session(cfg_debate)

    # 1. Turn count differentiation across every scenario
    assert res_silent.turns_used == 0, f"Scenario {scenario}: Silent mode used turns: {res_silent.turns_used}"
    assert res_debate.turns_used >= 1, f"Scenario {scenario}: Debate mode did not use debate turns: {res_debate.turns_used}"
    assert res_debate.turns_used > res_silent.turns_used

    # 2. Dialogue volume differentiation across every scenario
    assert len(res_debate.messages) > len(res_silent.messages), (
        f"Scenario {scenario}: Debate message count ({len(res_debate.messages)}) "
        f"should exceed silent count ({len(res_silent.messages)})"
    )

    # 3. Message typology differentiation
    silent_types = {m.msg_type for m in res_silent.messages}
    debate_types = {m.msg_type for m in res_debate.messages}

    # Silent mode contains only initial recommendations
    assert silent_types == {MsgType.RECOMMEND}
    # Debate mode contains deliberation rounds and final synthesized stances
    assert MsgType.FINAL in debate_types
