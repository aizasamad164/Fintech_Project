from app.optimization.discretize import discretize_allocation


def test_discretize_allocation_basic():
    budget = 1000.0
    weights = {"AAPL": 0.5, "MSFT": 0.5}
    prices = {"AAPL": 150.0, "MSFT": 300.0}

    result = discretize_allocation(budget, weights, prices)

    assert result["AAPL"]["shares"] == 3  # floor(500/150)
    assert result["MSFT"]["shares"] == 1  # floor(500/300)
