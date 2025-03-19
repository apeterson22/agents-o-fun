def new_strategy(data): return [{'profit': trade.get('expected_return', 0) * 1.1} for trade in data]
