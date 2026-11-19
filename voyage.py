"""Optimize a synthetic voyage on a discrete through-water speed grid."""
from dataclasses import dataclass
from math import ceil

SPEEDS = tuple(range(9, 19))
DEADLINES = tuple(range(13, 31))
CO2_FACTOR = 3.206


@dataclass(frozen=True)
class Leg:
    distance: int
    current: float
    load: float


ROUTES = {
    "calm": tuple(Leg(40, 0, 1) for _ in range(6)),
    "mixed": tuple(Leg(40, current, load) for current, load in
                   [(1.5, 1), (-1.5, 1.6), (1, .85), (-2, 1.8), (.5, .95), (1, .85)]),
    "headwind": tuple(Leg(40, current, load) for current, load in
                      [(-2, 1.4), (-2.5, 1.6), (-2, 1.7), (-1, 1.35), (-1.5, 1.5), (-1, 1.2)]),
}


@dataclass(frozen=True)
class Option:
    speed: int
    minutes: int
    fuel_grams: int


def leg_option(leg, speed):
    ground_speed = speed + leg.current
    if ground_speed <= 0:
        raise ValueError("Ground speed must be positive")
    hours = leg.distance / ground_speed
    tonnes_per_hour = .10 + .78 * leg.load * (speed / 14)**3
    return Option(speed, ceil(hours * 60), round(tonnes_per_hour * hours * 1_000_000))


def candidate_plans(route, speeds=SPEEDS):
    """At each elapsed minute keep the least-fuel plan and its speed sequence."""
    states = {0: (0, ())}
    for leg in route:
        next_states = {}
        for option in [leg_option(leg, speed) for speed in speeds]:
            for elapsed, (fuel, sequence) in states.items():
                time = elapsed + option.minutes
                candidate = (fuel + option.fuel_grams, sequence + (option.speed,))
                if time not in next_states or candidate < next_states[time]:
                    next_states[time] = candidate
        states = next_states
    return sorted((time, grams, speeds) for time, (grams, speeds) in states.items())


def constant_plans(route, speeds=SPEEDS):
    plans = []
    for speed in speeds:
        legs = [leg_option(leg, speed) for leg in route]
        plans.append((sum(o.minutes for o in legs), sum(o.fuel_grams for o in legs),
                      (speed,) * len(legs)))
    return plans


def best(plans, deadline):
    return min((plan for plan in plans if plan[0] <= deadline),
               key=lambda p: (p[1], p[0], p[2]), default=None)


def describe(route, plan):
    if plan is None:
        return None
    minutes, grams, speeds = plan
    return {
        "minutes": minutes, "fuel": round(grams / 1_000_000, 6),
        "co2": round(grams * CO2_FACTOR / 1_000_000, 6),
        "legs": [
            {"distance": leg.distance, "current": leg.current, "load": leg.load,
             "speed": speed, "ground": speed + leg.current,
             "minutes": option.minutes, "fuel": round(option.fuel_grams / 1_000_000, 6)}
            for leg, speed in zip(route, speeds)
            for option in [leg_option(leg, speed)]
        ],
    }


def experiment():
    result = {}
    for name, route in ROUTES.items():
        adaptive = candidate_plans(route)
        constant = constant_plans(route)
        result[name] = {
            "fastest": min(time for time, _, _ in adaptive),
            "plans": {str(h): {"adaptive": describe(route, best(adaptive, h*60)),
                               "constant": describe(route, best(constant, h*60))}
                      for h in DEADLINES},
        }
    return result
