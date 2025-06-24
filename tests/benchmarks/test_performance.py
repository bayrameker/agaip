"""Performance benchmarks for CI/CD pipeline."""

import pytest
import time


def test_basic_performance(benchmark):
    """Basic performance test."""
    def dummy_function():
        time.sleep(0.001)  # 1ms
        return "done"
    
    result = benchmark(dummy_function)
    assert result == "done"


def test_list_creation_performance(benchmark):
    """Test list creation performance."""
    def create_list():
        return [i for i in range(1000)]
    
    result = benchmark(create_list)
    assert len(result) == 1000
