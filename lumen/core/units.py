"""
Deterministic unit conversion engine for length, mass, temperature, speed, data size, and time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class UnitConversionResult:
    query: str
    from_val: float
    from_unit: str
    to_val: float
    to_unit: str
    formatted_result: str
    category: str


# Base unit multipliers for linear categories
LINEAR_UNITS: Dict[str, Dict[str, Tuple[float, str]]] = {
    "length": {
        "m": (1.0, "m"),
        "meter": (1.0, "m"),
        "meters": (1.0, "m"),
        "km": (1000.0, "km"),
        "kilometer": (1000.0, "km"),
        "kilometers": (1000.0, "km"),
        "cm": (0.01, "cm"),
        "centimeter": (0.01, "cm"),
        "centimeters": (0.01, "cm"),
        "mm": (0.001, "mm"),
        "millimeter": (0.001, "mm"),
        "millimeters": (0.001, "mm"),
        "mi": (1609.344, "miles"),
        "mile": (1609.344, "miles"),
        "miles": (1609.344, "miles"),
        "yd": (0.9144, "yards"),
        "yard": (0.9144, "yards"),
        "yards": (0.9144, "yards"),
        "ft": (0.3048, "feet"),
        "foot": (0.3048, "feet"),
        "feet": (0.3048, "feet"),
        "in": (0.0254, "inches"),
        "inch": (0.0254, "inches"),
        "inches": (0.0254, "inches"),
        "nmi": (1852.0, "nmi"),
    },
    "mass": {
        "g": (1.0, "g"),
        "gram": (1.0, "g"),
        "grams": (1.0, "g"),
        "kg": (1000.0, "kg"),
        "kilogram": (1000.0, "kg"),
        "kilograms": (1000.0, "kg"),
        "mg": (0.001, "mg"),
        "milligram": (0.001, "mg"),
        "milligrams": (0.001, "mg"),
        "lb": (453.59237, "lbs"),
        "lbs": (453.59237, "lbs"),
        "pound": (453.59237, "lbs"),
        "pounds": (453.59237, "lbs"),
        "oz": (28.349523125, "oz"),
        "ounce": (28.349523125, "oz"),
        "ounces": (28.349523125, "oz"),
        "ton": (1000000.0, "tons"),
        "tonne": (1000000.0, "tons"),
        "tons": (1000000.0, "tons"),
    },
    "speed": {
        "m/s": (1.0, "m/s"),
        "mps": (1.0, "m/s"),
        "km/h": (1.0 / 3.6, "km/h"),
        "kmh": (1.0 / 3.6, "km/h"),
        "kph": (1.0 / 3.6, "km/h"),
        "mph": (0.44704, "mph"),
        "knot": (0.514444, "knots"),
        "knots": (0.514444, "knots"),
    },
    "data": {
        "b": (1.0, "B"),
        "byte": (1.0, "B"),
        "bytes": (1.0, "B"),
        "kb": (1000.0, "KB"),
        "kilobyte": (1000.0, "KB"),
        "kilobytes": (1000.0, "KB"),
        "mb": (1000000.0, "MB"),
        "megabyte": (1000000.0, "MB"),
        "megabytes": (1000000.0, "MB"),
        "gb": (1000000000.0, "GB"),
        "gigabyte": (1000000000.0, "GB"),
        "gigabytes": (1000000000.0, "GB"),
        "tb": (1000000000000.0, "TB"),
        "terabyte": (1000000000000.0, "TB"),
        "terabytes": (1000000000000.0, "TB"),
        "kib": (1024.0, "KiB"),
        "mib": (1048576.0, "MiB"),
        "gib": (1073741824.0, "GiB"),
        "tib": (1099511627776.0, "TiB"),
    },
    "time": {
        "s": (1.0, "seconds"),
        "sec": (1.0, "seconds"),
        "second": (1.0, "seconds"),
        "seconds": (1.0, "seconds"),
        "min": (60.0, "minutes"),
        "minute": (60.0, "minutes"),
        "minutes": (60.0, "minutes"),
        "h": (3600.0, "hours"),
        "hr": (3600.0, "hours"),
        "hour": (3600.0, "hours"),
        "hours": (3600.0, "hours"),
        "d": (86400.0, "days"),
        "day": (86400.0, "days"),
        "days": (86400.0, "days"),
        "wk": (604800.0, "weeks"),
        "week": (604800.0, "weeks"),
        "weeks": (604800.0, "weeks"),
        "yr": (31536000.0, "years"),
        "year": (31536000.0, "years"),
        "years": (31536000.0, "years"),
    },
    "area": {
        "sqm": (1.0, "sq m"),
        "sq m": (1.0, "sq m"),
        "m2": (1.0, "sq m"),
        "sqkm": (1000000.0, "sq km"),
        "sq km": (1000000.0, "sq km"),
        "km2": (1000000.0, "sq km"),
        "sqft": (0.092903, "sq ft"),
        "sq ft": (0.092903, "sq ft"),
        "ft2": (0.092903, "sq ft"),
        "ha": (10000.0, "hectares"),
        "hectare": (10000.0, "hectares"),
        "hectares": (10000.0, "hectares"),
        "acre": (4046.8564224, "acres"),
        "acres": (4046.8564224, "acres"),
    },
    "volume": {
        "l": (1.0, "L"),
        "liter": (1.0, "L"),
        "liters": (1.0, "L"),
        "litre": (1.0, "L"),
        "litres": (1.0, "L"),
        "ml": (0.001, "ml"),
        "milliliter": (0.001, "ml"),
        "milliliters": (0.001, "ml"),
        "gal": (3.785411784, "gallons"),
        "gallon": (3.785411784, "gallons"),
        "gallons": (3.785411784, "gallons"),
        "cup": (0.2365882365, "cups"),
        "cups": (0.2365882365, "cups"),
    },
}

TEMP_UNITS = {"c", "celsius", "f", "fahrenheit", "k", "kelvin"}


def _convert_temperature(val: float, from_u: str, to_u: str) -> Optional[float]:
    """Converts between Celsius, Fahrenheit, and Kelvin."""
    from_u = from_u.lower().lstrip("°")
    to_u = to_u.lower().lstrip("°")

    # Convert from_u to Celsius first
    if from_u in ("c", "celsius"):
        c = val
    elif from_u in ("f", "fahrenheit"):
        c = (val - 32.0) * (5.0 / 9.0)
    elif from_u in ("k", "kelvin"):
        c = val - 273.15
    else:
        return None

    # Convert Celsius to to_u
    if to_u in ("c", "celsius"):
        return c
    elif to_u in ("f", "fahrenheit"):
        return (c * (9.0 / 5.0)) + 32.0
    elif to_u in ("k", "kelvin"):
        return c + 273.15
    return None


def parse_and_convert_unit(query: str) -> Optional[UnitConversionResult]:
    """
    Parses queries like '100 km in miles', '72 F in C', '50 km/h to mph', '2 GB to MB'.
    """
    if not query or len(query.strip()) < 3:
        return None

    pattern = r"^\s*([\d\.\-]+)\s*([a-zA-Z°/][a-zA-Z0-9°/\s]*?)\s+(?:in|to|=|as)\s+([a-zA-Z°/][a-zA-Z0-9°/\s]*?)\s*$"
    m = re.match(pattern, query.strip(), re.IGNORECASE)
    if not m:
        return None

    try:
        val = float(m.group(1))
    except ValueError:
        return None

    u_from = m.group(2).strip().lower()
    u_to = m.group(3).strip().lower()

    # Check Temperature
    if u_from in TEMP_UNITS and u_to in TEMP_UNITS:
        converted = _convert_temperature(val, u_from, u_to)
        if converted is not None:
            from_display = f"{val:g}°{u_from.upper()[:1]}"
            to_display = f"{converted:.2f}°{u_to.upper()[:1]}" if abs(converted - round(converted)) > 0.001 else f"{round(converted):g}°{u_to.upper()[:1]}"
            res_str = f"{from_display} = {to_display}"
            return UnitConversionResult(
                query=query,
                from_val=val,
                from_unit=u_from,
                to_val=converted,
                to_unit=u_to,
                formatted_result=res_str,
                category="Temperature",
            )

    # Check Linear Units
    for cat_name, unit_map in LINEAR_UNITS.items():
        if u_from in unit_map and u_to in unit_map:
            mult_from, display_from = unit_map[u_from]
            mult_to, display_to = unit_map[u_to]

            base_val = val * mult_from
            target_val = base_val / mult_to

            # Format float nicely
            if target_val.is_integer() and abs(target_val) < 1e12:
                formatted_to = f"{int(target_val):,}"
            elif abs(target_val) < 0.0001 or abs(target_val) > 1e9:
                formatted_to = f"{target_val:.4e}"
            else:
                formatted_to = f"{target_val:.4g}"

            from_str = f"{val:g} {display_from}"
            to_str = f"{formatted_to} {display_to}"
            return UnitConversionResult(
                query=query,
                from_val=val,
                from_unit=display_from,
                to_val=target_val,
                to_unit=display_to,
                formatted_result=f"{from_str} = {to_str}",
                category=cat_name.title(),
            )

    return None
