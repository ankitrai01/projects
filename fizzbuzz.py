from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterator
import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Rule:
    """A single divisibility rule mapping a divisor to an output word"""      
    divisor: int
    word: str

    def __post_init__(self) -> None:
        if self.divisor <= 0:
            raise ValueError(f"Divisor must be positive, got {self.divisor}")


@dataclass
class FizzBuzzSolver:
    """ Solver FizzBuzz for an arbitrary set of divisibility rules."""
    rules: list[Rule] = field(
        default_factory=lambda: [Rule(3, "Fizz"), Rule(5, "Buzz")]
    )

    def evaluate(self, n: int) -> str:
        """ Return the FizzBuzz output for a single number."""
        result = "".join(rule.word for rule in self.rules if n % rule.divisor == 0)
        return result or str(n)

    def solve(self, start: int, end: int) -> Iterator[str]:
        """ Lazily yield Fizzbuzz outputs for a range of numbers."""
        if start > end:
            raise ValueError(f"Start must be less than or equal to end")
        for n in range(start, end + 1):
            yield self.evaluate(n)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description= "Run fizzbuzz over a range.")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=100)
    parser.add_argument("--fizz-divisor", type=int, default=3)
    parser.add_argument("--buzz-divisor", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    solver = FizzBuzzSolver(
        rules=[Rule(args.fizz_divisor, "Fizz"), Rule(args.buzz_divisor, "Buzz")]
    )
    logger.info("Running FizzBuzz from %d to %d", args.start, args.end)

    output = "\n".join(solver.solve(args.start, args.end))
    sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()

        