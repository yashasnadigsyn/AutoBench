import random
from pydantic import BaseModel, Field
from typing import List, Optional

from src.config import DAY_NAMES, SHIFT_DURATION_MINUTES
from src.simulation.shift import (
    add_minutes,
    calculate_deadhead,
    ride_fits_in_shift,
)


class RideEvent(BaseModel):
    origin: str
    destination: str
    distance_km: float
    base_duration_min: float
    simulated_duration_min: float
    fare: float
    fuel_cost: float
    profit: float
    time_started: str
    time_ended: str


class GameState(BaseModel):
    current_day: int = 1
    current_time: str = "05:00"
    current_location: str = "Majestic"
    bank_balance: float = 0.0
    shift_remaining_minutes: int = SHIFT_DURATION_MINUTES
    day_of_week: int = 0

    today_rides: int = 0
    today_gross: float = 0.0
    today_fuel: float = 0.0
    today_deadhead: float = 0.0
    shift_start_time: str = ""

    rides_history: List[RideEvent] = Field(default_factory=list)

    def start_day(self, day: int, start_time: str = "07:00"):
        self.current_day = day
        self.day_of_week = (day - 1) % 7
        self.current_time = start_time
        self.shift_start_time = start_time
        self.shift_remaining_minutes = SHIFT_DURATION_MINUTES
        self.current_location = "Majestic"

        self.today_rides = 0
        self.today_gross = 0.0
        self.today_fuel = 0.0
        self.today_deadhead = 0.0
        self.rides_history = []

    def get_shift_remaining_str(self) -> str:
        hours = self.shift_remaining_minutes // 60
        minutes = self.shift_remaining_minutes % 60
        return f"{hours}h {minutes}m"

    def can_accept_ride(self, ride_duration_min: int) -> bool:
        return ride_fits_in_shift(
            self.current_time, ride_duration_min, self.shift_remaining_minutes
        )

    def accept_ride(
        self,
        destination: str,
        distance_km: float,
        base_duration_min: float,
        simulated_duration_min: float,
        fare: float,
        fuel_cost: float,
    ) -> RideEvent:
        profit = fare - fuel_cost

        time_started = self.current_time
        time_ended = add_minutes(self.current_time, int(simulated_duration_min))

        ride = RideEvent(
            origin=self.current_location,
            destination=destination,
            distance_km=distance_km,
            base_duration_min=base_duration_min,
            simulated_duration_min=simulated_duration_min,
            fare=fare,
            fuel_cost=fuel_cost,
            profit=profit,
            time_started=time_started,
            time_ended=time_ended,
        )

        self.rides_history.append(ride)

        self.current_location = destination
        self.current_time = time_ended
        self.bank_balance += profit
        self.today_rides += 1
        self.today_gross += fare
        self.today_fuel += fuel_cost
        self.shift_remaining_minutes -= int(simulated_duration_min)

        return ride

    def end_shift(
        self,
        idle_wait_min: int = 0,
        is_rainy: bool = False,
        rng: Optional[random.Random] = None,
    ) -> float:
        self.current_time = add_minutes(self.current_time, idle_wait_min)
        self.shift_remaining_minutes -= idle_wait_min

        if self.current_location != "Majestic":
            deadhead_cost = calculate_deadhead(
                self.current_location, "Majestic", self.current_time, self.day_of_week,
                is_rainy=is_rainy, rng=rng,
            )
            self.bank_balance -= deadhead_cost
            self.today_deadhead = deadhead_cost
            return deadhead_cost

        return 0.0

    def advance_time(self, minutes: int):
        self.current_time = add_minutes(self.current_time, minutes)
        self.shift_remaining_minutes -= minutes

    def get_day_summary(self) -> str:
        net_profit = self.today_gross - self.today_fuel - self.today_deadhead

        return (
            f"Day {self.current_day} ({DAY_NAMES[self.day_of_week]}): "
            f"Shift {self.shift_start_time} to {self.current_time}. "
            f"Ended at: {self.current_location}. "
            f"Rides: {self.today_rides}. Gross: ₹{self.today_gross:.0f}. "
            f"Fuel (Rides): ₹{self.today_fuel:.0f}. "
            f"Deadhead Fuel: ₹{self.today_deadhead:.0f}. "
            f"Net Profit Day {self.current_day}: ₹{net_profit:.0f}. "
            f"Total Bank Balance: ₹{self.bank_balance:.0f}."
        )
