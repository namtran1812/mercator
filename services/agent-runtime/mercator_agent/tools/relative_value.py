from __future__ import annotations

from datetime import date
import math
import statistics

from mercator_agent.state.models import (
    InstrumentProfile,
    PriceObservation,
    RelativeValueResult,
)


_RATING_ORDER = {
    "AAA": 0,
    "AA+": 1,
    "AA": 2,
    "AA-": 3,
    "A+": 4,
    "A": 5,
    "A-": 6,
    "BBB+": 7,
    "BBB": 8,
    "BBB-": 9,
    "BB+": 10,
    "BB": 11,
    "BB-": 12,
    "B+": 13,
    "B": 14,
    "B-": 15,
    "CCC+": 16,
    "CCC": 17,
    "CCC-": 18,
}


def _rating_distance(
    left: str | None,
    right: str | None,
) -> int | None:
    if (
        left is None
        or right is None
    ):
        return None

    left_value = _RATING_ORDER.get(
        left.upper()
    )

    right_value = _RATING_ORDER.get(
        right.upper()
    )

    if (
        left_value is None
        or right_value is None
    ):
        return None

    return abs(
        left_value
        - right_value
    )


def _maturity_distance_years(
    left: date | None,
    right: date | None,
) -> float | None:
    if (
        left is None
        or right is None
    ):
        return None

    return abs(
        (
            left
            - right
        ).days
    ) / 365.25


def _peer_score(
    target: InstrumentProfile,
    candidate: InstrumentProfile,
) -> float:
    score = 0.0

    if (
        target.instrument_type
        == candidate.instrument_type
    ):
        score += 3.0

    if (
        target.currency
        == candidate.currency
    ):
        score += 2.0

    if (
        target.sector
        and candidate.sector
        and target.sector
        == candidate.sector
    ):
        score += 4.0

    maturity_distance = (
        _maturity_distance_years(
            target.maturity_date,
            candidate.maturity_date,
        )
    )

    if maturity_distance is not None:
        score += max(
            0.0,
            3.0
            - maturity_distance,
        )

    rating_distance = (
        _rating_distance(
            target.rating,
            candidate.rating,
        )
    )

    if rating_distance is not None:
        score += max(
            0.0,
            3.0
            - rating_distance,
        )

    return score


def _confidence(
    peer_count: int,
    *,
    has_sector: bool,
    has_rating: bool,
    has_maturity: bool,
    spread_standard_deviation_bps: float | None = None,
) -> str:
    metadata_dimensions = sum(
        (
            has_sector,
            has_rating,
            has_maturity,
        )
    )

    #
    # Large peer dispersion means the peer universe is
    # economically heterogeneous even if the raw peer
    # count is high.
    #
    if (
        spread_standard_deviation_bps
        is not None
        and spread_standard_deviation_bps
        >= 75.0
    ):
        return "LOW"

    if (
        spread_standard_deviation_bps
        is not None
        and spread_standard_deviation_bps
        >= 40.0
    ):
        return "MEDIUM"

    if (
        peer_count >= 8
        and metadata_dimensions >= 2
    ):
        return "HIGH"

    if (
        peer_count >= 4
        and metadata_dimensions >= 1
    ):
        return "MEDIUM"

    return "LOW"


def _classification(
    spread_difference_bps: float,
    spread_z_score: float | None,
) -> str:
    #
    # Require both economic magnitude and statistical
    # evidence when dispersion is available.
    #
    if spread_z_score is not None:
        if (
            spread_difference_bps >= 15.0
            and spread_z_score >= 1.0
        ):
            return "CHEAP"

        if (
            spread_difference_bps <= -15.0
            and spread_z_score <= -1.0
        ):
            return "RICH"

        return "FAIR"

    #
    # Degenerate / tiny peer samples fall back to a
    # conservative absolute threshold.
    #
    if spread_difference_bps >= 25.0:
        return "CHEAP"

    if spread_difference_bps <= -25.0:
        return "RICH"

    return "FAIR"


def calculate_relative_value(
    prices: list[PriceObservation],
    *,
    profiles: list[
        InstrumentProfile
    ] | None = None,
    target_instrument_ids: list[
        int
    ] | None = None,
    maximum_peers: int = 20,
) -> list[RelativeValueResult]:
    """
    Calculate peer-aware relative value.

    When profiles are omitted, retain legacy global-peer
    behavior for backwards compatibility.
    """

    valid_prices = [
        price
        for price in prices
        if (
            price.quality_status
            == "VALID"
            and price.quality_score
            >= 0.80
        )
    ]

    if len(valid_prices) < 2:
        return []

    price_by_id = {
        price.instrument_id:
            price
        for price in valid_prices
    }

    #
    # --------------------------------------------------------
    # Legacy compatibility path
    # --------------------------------------------------------
    #
    if not profiles:
        average_spread = statistics.mean(
            price.g_spread_bps
            for price in valid_prices
        )

        results = []

        for price in valid_prices:
            difference = (
                price.g_spread_bps
                - average_spread
            )

            classification = (
                _classification(
                    difference,
                    None,
                )
            )

            results.append(
                RelativeValueResult(
                    instrument_id=
                        price.instrument_id,

                    spread_bps=
                        price.g_spread_bps,

                    peer_average_spread_bps=
                        average_spread,

                    peer_median_spread_bps=
                        statistics.median(
                            item.g_spread_bps
                            for item
                            in valid_prices
                        ),

                    spread_difference_bps=
                        difference,

                    peer_count=
                        len(valid_prices) - 1,

                    classification=
                        classification,

                    confidence="LOW",

                    interpretation=(
                        "trades materially wider than "
                        "the selected peer average"
                        if classification == "CHEAP"
                        else (
                            "trades materially tighter "
                            "than the selected peer average"
                            if classification == "RICH"
                            else (
                                "trades near the selected "
                                "peer average"
                            )
                        )
                    ),
                )
            )

        return sorted(
            results,
            key=lambda result:
                result.spread_difference_bps,
            reverse=True,
        )

    profile_by_id = {
        profile.instrument_id:
            profile
        for profile in profiles
    }

    targets = (
        list(
            dict.fromkeys(
                target_instrument_ids
            )
        )
        if target_instrument_ids
        else list(
            price_by_id
        )
    )

    results: list[
        RelativeValueResult
    ] = []

    for instrument_id in targets:
        target_price = (
            price_by_id.get(
                instrument_id
            )
        )

        target_profile = (
            profile_by_id.get(
                instrument_id
            )
        )

        if (
            target_price is None
            or target_profile is None
        ):
            continue

        candidates = []

        for candidate_id, candidate_price in (
            price_by_id.items()
        ):
            if candidate_id == instrument_id:
                continue

            candidate_profile = (
                profile_by_id.get(
                    candidate_id
                )
            )

            if candidate_profile is None:
                continue

            if (
                candidate_profile.instrument_type
                != target_profile.instrument_type
            ):
                continue

            if (
                candidate_profile.currency
                != target_profile.currency
            ):
                continue

            if (
                target_profile.sector
                and candidate_profile.sector
                and candidate_profile.sector
                != target_profile.sector
            ):
                continue

            maturity_distance = (
                _maturity_distance_years(
                    target_profile.maturity_date,
                    candidate_profile.maturity_date,
                )
            )

            rating_distance = (
                _rating_distance(
                    target_profile.rating,
                    candidate_profile.rating,
                )
            )

            candidates.append(
                (
                    _peer_score(
                        target_profile,
                        candidate_profile,
                    ),
                    candidate_profile,
                    candidate_price,
                    maturity_distance,
                    rating_distance,
                )
            )

        #
        # Progressive peer construction:
        #
        # Tier 1:
        #   rating +/-1 notch
        #   maturity +/-2 years
        #
        # Tier 2:
        #   rating +/-2 notches
        #   maturity +/-3 years
        #
        # Only widen the universe when Tier 1 does not
        # provide enough observations.
        #

        def eligible(
            item,
            *,
            maximum_rating_distance: int,
            maximum_maturity_distance: float,
        ) -> bool:
            maturity_distance = item[3]
            rating_distance = item[4]

            if (
                maturity_distance is not None
                and maturity_distance
                > maximum_maturity_distance
            ):
                return False

            if (
                rating_distance is not None
                and rating_distance
                > maximum_rating_distance
            ):
                return False

            return True


        tier_one = [
            item
            for item in candidates
            if eligible(
                item,
                maximum_rating_distance=1,
                maximum_maturity_distance=2.0,
            )
        ]

        if len(tier_one) >= 5:
            candidates = tier_one
        else:
            candidates = [
                item
                for item in candidates
                if eligible(
                    item,
                    maximum_rating_distance=2,
                    maximum_maturity_distance=3.0,
                )
            ]

        #
        # Prefer external issuers when enough are available,
        # avoiding same-issuer capital-structure clustering.
        #
        external = [
            item
            for item in candidates
            if (
                item[1].issuer_name
                != target_profile.issuer_name
            )
        ]

        if len(external) >= 3:
            candidates = external

        candidates.sort(
            key=lambda item: (
                item[4]
                if item[4] is not None
                else 99,

                item[3]
                if item[3] is not None
                else 99.0,

                -item[0],

                item[1].instrument_id,
            )
        )

        candidates = candidates[
            :min(
                maximum_peers,
                15,
            )
        ]

        if len(candidates) < 2:
            continue

        peer_prices = [
            item[2]
            for item in candidates
        ]

        peer_spreads = [
            item.g_spread_bps
            for item in peer_prices
        ]

        average_spread = (
            statistics.mean(
                peer_spreads
            )
        )

        median_spread = (
            statistics.median(
                peer_spreads
            )
        )

        difference = (
            target_price.g_spread_bps
            - median_spread
        )

        standard_deviation = None
        z_score = None

        if len(peer_spreads) >= 2:
            value = statistics.pstdev(
                peer_spreads
            )

            if value > 1e-12:
                standard_deviation = value

                z_score = (
                    difference
                    / value
                )

        classification = (
            _classification(
                difference,
                z_score,
            )
        )

        confidence = _confidence(
            len(candidates),

            has_sector=(
                target_profile.sector
                is not None
            ),

            has_rating=(
                target_profile.rating
                is not None
            ),

            has_maturity=(
                target_profile.maturity_date
                is not None
            ),

            spread_standard_deviation_bps=
                standard_deviation,
        )

        if classification == "CHEAP":
            interpretation = (
                "trades wider than its metadata-matched "
                "peer universe and screens relatively cheap"
            )

        elif classification == "RICH":
            interpretation = (
                "trades tighter than its metadata-matched "
                "peer universe and screens relatively rich"
            )

        else:
            interpretation = (
                "trades broadly in line with its "
                "metadata-matched peer universe"
            )

        results.append(
            RelativeValueResult(
                instrument_id=
                    target_price.instrument_id,

                spread_bps=
                    target_price.g_spread_bps,

                peer_average_spread_bps=
                    average_spread,

                peer_median_spread_bps=
                    median_spread,

                peer_standard_deviation_bps=
                    standard_deviation,

                spread_difference_bps=
                    difference,

                spread_z_score=
                    z_score,

                peer_count=
                    len(candidates),

                classification=
                    classification,

                confidence=
                    confidence,

                sector=
                    target_profile.sector,

                rating=
                    target_profile.rating,

                maturity_date=
                    target_profile.maturity_date,

                peer_instrument_ids=[
                    item[1].instrument_id
                    for item in candidates
                ],

                interpretation=
                    interpretation,
            )
        )

    return sorted(
        results,
        key=lambda result: (
            result.spread_z_score
            if result.spread_z_score
            is not None
            else (
                result.spread_difference_bps
                / 25.0
            )
        ),
        reverse=True,
    )
