#!/usr/bin/env python3

import os
import requests
from datetime import datetime as dt

from assistant.utils import thread

APIKEY_WEATHER = os.environ["APIKEY_WEATHER"]


INTERVALS = {
    "north east": (22.5, 67.5),
    "east": (67.5, 112.5),
    "south east": (112.5, 157.5),
    "south": (157.5, 202.5),
    "south west": (202.5, 247.5),
    "west": (247.5, 292.5),
    "north west": (292.5, 337.5),
}


def direction(degree):
    """Derive side of the world from a degree."""

    def belongs(n, interval):
        return True if interval[0] < n <= interval[1] else False

    if not belongs(degree, (0, 360)):
        raise ValueError(f"input degree {degree} does not belong [0, 360]")

    for direction in INTERVALS:
        return direction if belongs(degree, INTERVALS[direction]) else "north"


class WeatherRecord(object):
    def __init__(self, r):
        statements = [
            "self.temp = round(r['main']['temp'])",
            "self.temp_max = round(r['main']['temp_max'])",
            "self.temp_min = round(r['main']['temp_min'])",
            "self.pressure = int(r['main']['pressure'] * 0.75)",
            "self.humidity = r['main']['humidity']",
            "self.sunrise = None",
            "self.sunset = None",
            "self.conditions = [x['description'] for x in r['weather']]",
            "self.wind_deg = r['wind']['deg']",
            "self.wind_dir = direction(self.wind_deg)",
            "self.wind_speed = r['wind']['speed']",
            "self.dt = dt.utcfromtimestamp(r['dt'])",
        ]

        for statement in statements:
            try:
                exec(statement)
            except Exception:
                variable = statement.split(" = ")[0]
                exec(f"{variable} = None")
                # traceback.print_exc()


class Weather(WeatherRecord):
    def __init__(self, city=None, coordinates=None, zip=None):
        arguments = {}
        if city:
            arguments["q"] = city
            self.city = city
        if coordinates:
            self.lan, self.lon = coordinates
            arguments["lat"], arguments["lon"] = coordinates
        if zip:
            self.zip = zip
            arguments["zip"] = zip

        self.params = "&".join(f"{key}={arguments[key]}" for key in arguments)
        self.params += f"&units=metric&APPID={APIKEY_WEATHER}"
        thread((self.__current, self.__forecast), wait_to_finish=True)

    def __current(self):
        record = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?{self.params}"
        ).json()
        WeatherRecord.__init__(self, record)

    def __forecast(self):
        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/forecast?{self.params}"
        ).json()
        records = r["list"]
        r1 = WeatherRecord(records[0])
        self.forecasts = [[r1], [], [], [], [], []]
        count = 0
        for record in records[1:]:
            current = dt.utcfromtimestamp(record["dt"])
            previous = self.forecasts[count][-1].dt
            if current.day != previous.day:
                count += 1
            self.forecasts[count].append(WeatherRecord(record))

    def __str__(self):
        conditions = ", ".join(self.conditions)
        return f"""
Temperature:
           current        {self.temp} °C
                max        {self.temp_max} °C
                min        {self.temp_min} °C

Conditions:           {conditions}

Wind:                     {self.wind_speed} m/s, {self.wind_dir}

Pressure:              {self.pressure} mmHg

Humidity:              {self.humidity} %

Sunrise:                {self.sunrise}

Sunset:                 {self.sunset}
"""

    def summary(self):
        if self.temp_max - self.temp_min >= 3:
            summary = f"""
            You can observe {self.conditions[0]} in {self.city} right now,
            the temperature varies between {self.temp_min} and {self.temp_max}
            and is currently {self.temp} degrees"""
        else:
            summary = f"""
            You can observe {self.conditions[0]} in {self.city} right now,
            the temperature is currently {self.temp} degrees"""
        return summary

    def tempSummary(self):
        return f"The current temperature in {self.city} is {self.temp} degrees"

    def fullSummary(self):
        if self.temp_max - self.temp_min >= 3:
            opts = f"""
            Current temperature in {self.city} is {self.temp} degrees,
            you can observe {self.conditions[0]}.
            The {self.wind_dir}ern wind's speed is {self.wind_speed}
            meters per second. Humidity is {self.humidity} %"""
        else:
            opts = f"""
            The temperature in {self.city} varies between
            {self.temp_min} and {self.temp_max} today and
            is currently {self.temp} degrees.
            You can observe {self.conditions[0]}.
            The {self.wind_dir}ern wind's speed is {self.wind_speed}
            meters per second. Humidity is {self.humidity} %"""
        return opts

    def max(self, days_ahead=0):
        return max([temp.temp for temp in self.forecasts[days_ahead]])

    def min(self, days_ahead=0, daily=True):
        if daily:
            return min([temp.temp for temp in self.forecasts[days_ahead]])
        else:
            return min(
                [temp.temp for temp in self.forecasts[days_ahead] if temp]
            )

    def aver(self, days_ahead=0):
        res = [temp.temp for temp in self.forecasts[days_ahead]]
        return sum(res) / len(res)

    def forecast(self, days_ahead=0, hour=12):
        self.forecasts[days_ahead][int(hour / 3)]
