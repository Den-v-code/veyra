"""Independent finite resource oracle for the current autonomous feedback grammar."""

from itertools import product

from src.core.prime_power_observer_genesis_p3og import TransitionKind


def _terminal(period: int, credit: int, high: TransitionKind, low: TransitionKind):
    phase = 0
    current_credit = credit
    initial = (phase, current_credit)
    departed = False
    seen: set[tuple[int, int]] = set()
    bound = period + credit - 1

    for tick in range(1, bound + 1):
        kind = low if current_credit == 1 else high
        if kind is TransitionKind.ADVANCE:
            phase = (phase + 1) % period
        elif kind is TransitionKind.MAINTAIN:
            current_credit = credit
        else:
            current_credit -= 1
            if current_credit <= 0:
                return "removed", tick

        current = (phase, current_credit)
        if current == initial:
            return ("witnessed" if departed else "never-departs"), tick
        departed = True
        if current in seen:
            return "cycle", tick
        seen.add(current)

    raise AssertionError("reachable feedback trajectory escaped committed bound")


def test_all_supported_reachable_feedback_paths_fit_126_ticks() -> None:
    runs = 0
    maximum = 0
    for high, low, disabled_high, disabled_low in product(
        tuple(TransitionKind), repeat=4,
    ):
        # Disabled rows are deliberately enumerated even though a fresh
        # pre-coupling formation genealogy cannot reach them. Their presence
        # must not change the reachable ACTIVE trajectory.
        assert disabled_high in tuple(TransitionKind)
        assert disabled_low in tuple(TransitionKind)
        for period in range(1, 64):
            for credit in range(1, 65):
                _, ticks = _terminal(period, credit, high, low)
                runs += 1
                maximum = max(maximum, ticks)
                assert ticks <= period + credit - 1 <= 126

    assert runs == 81 * 63 * 64
    assert maximum == 126
