import pytest
from fizzbuzz import FizzBuzzSolver, Rule


class TestFizzBuzzSolver:
    def setup_method(self):
        self.solver = FizzBuzzSolver()

    @pytest.mark.parametrize("n,expected", [
        (1, "1"),
        (3, "Fizz"),
        (5, "Buzz"),
        (15, "FizzBuzz"),
        (7, "7"),
    ])
    def test_evaluate(self, n, expected):
        assert self.solver.evaluate(n) == expected

    def test_solve_range(self):
        result = list(self.solver.solve(1, 15))
        assert result[-1] == "FizzBuzz"
        assert len(result) == 15

    def test_invalid_range_raises(self):
        with pytest.raises(ValueError):
            list(self.solver.solve(10, 1))

    def test_custom_rules(self):
        solver = FizzBuzzSolver(rules=[Rule(7, "Bazz")])
        assert solver.evaluate(14) == "Bazz"
        assert solver.evaluate(15) == "15"