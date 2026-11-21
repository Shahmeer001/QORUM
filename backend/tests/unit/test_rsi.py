from app.signals.rsi import calculate_rsi


def test_rsi_bounds_and_trends():
    # Steadily rising prices -> RSI high (> 60)
    rising = [100.0 + i * 2.0 for i in range(30)]
    rsi_rising = calculate_rsi(rising)
    assert 60.0 <= rsi_rising <= 100.0

    # Steadily falling prices -> RSI low (< 40)
    falling = [200.0 - i * 2.0 for i in range(30)]
    rsi_falling = calculate_rsi(falling)
    assert 0.0 <= rsi_falling <= 40.0

    # Constant flat prices
    flat = [100.0] * 30
    rsi_flat = calculate_rsi(flat)
    assert 40.0 <= rsi_flat <= 60.0
