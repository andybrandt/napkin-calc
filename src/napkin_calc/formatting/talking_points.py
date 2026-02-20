"""Generate human-friendly "talking point" strings from exact values.

During an interview the candidate needs to speak in rounded magnitudes:
"about 120 per second", "roughly 3.5 billion per year", etc.
This module converts a Decimal into that kind of phrase.

Also handles data sizes: given a byte count and unit, produces phrases
like "~1.5 PB" or "~400 GB".
"""

from decimal import Decimal, ROUND_HALF_UP

from napkin_calc.core.constants import DataSizeUnit


# Magnitude tiers ordered from largest to smallest so we match the
# highest applicable scale first.
_MAGNITUDE_TIERS: list[tuple[Decimal, str]] = [
    (Decimal("1E18"), "quintillion"),
    (Decimal("1E15"), "quadrillion"),
    (Decimal("1E12"), "trillion"),
    (Decimal("1E9"),  "billion"),
    (Decimal("1E6"),  "million"),
    (Decimal("1E3"),  "thousand"),
]


class TalkingPointGenerator:
    """Convert a numeric value into an interview-friendly phrase."""

    @staticmethod
    def generate_data_size(value: Decimal, unit: DataSizeUnit) -> str:
        """Return a speakable string for a data size.

        Parameters
        ----------
        value :
            The numeric amount (already in *unit*).
        unit :
            The data-size unit (B, KB, MB, ...).

        Examples
        --------
        >>> TalkingPointGenerator.generate_data_size(Decimal("1.5"), DataSizeUnit.PETABYTE)
        '~1.5 PB'
        >>> TalkingPointGenerator.generate_data_size(Decimal("400"), DataSizeUnit.GIGABYTE)
        '~400 GB'
        """
        if value == 0:
            return "0"

        rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        if rounded == rounded.to_integral_value():
            int_value = int(rounded)
            if value == rounded:
                return f"{int_value} {unit.value}"
            return f"~{int_value} {unit.value}"

        display = f"{rounded.normalize()}"
        return f"~{display} {unit.value}"

    @staticmethod
    def generate(value: Decimal) -> str:
        """Return a rounded, speakable string for *value*.

        Examples
        --------
        >>> TalkingPointGenerator.generate(Decimal("115"))
        '~115'
        >>> TalkingPointGenerator.generate(Decimal("6944"))
        '~6.9 thousand'
        >>> TalkingPointGenerator.generate(Decimal("10000000"))
        '10 million'
        >>> TalkingPointGenerator.generate(Decimal("3650000000"))
        '~3.7 billion'
        """
        if value == 0:
            return "0"

        abs_value = abs(value)
        sign_prefix = "-" if value < 0 else ""

        for threshold, label in _MAGNITUDE_TIERS:
            if abs_value >= threshold:
                scaled = abs_value / threshold
                return sign_prefix + _format_scaled(scaled, label)

        # Below 1,000 – just round sensibly
        rounded = _round_small(abs_value)
        return f"{sign_prefix}~{rounded}"


def _format_scaled(scaled: Decimal, label: str) -> str:
    """Format a value that has been divided by its magnitude tier.

    If the scaled number is a clean integer (e.g. exactly 10 million)
    we omit the "~" prefix.  Otherwise we round to one decimal and
    prefix with "~".
    """
    # Round to one decimal place for the spoken phrase
    rounded = scaled.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    if rounded == rounded.to_integral_value():
        int_value = int(rounded)
        if scaled == rounded:
            return f"{int_value} {label}"
        return f"~{int_value} {label}"

    # Strip trailing zeros (e.g. "3.0" -> keep as int above, "3.5" stays)
    display = f"{rounded.normalize()}"
    return f"~{display} {label}"


def _round_small(value: Decimal) -> str:
    """Round a sub-thousand value for spoken output.

    Values >= 10 are shown as whole numbers; smaller values keep
    one decimal place.
    """
    if value >= 10:
        return str(int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
    rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP).normalize()
    return str(rounded)
