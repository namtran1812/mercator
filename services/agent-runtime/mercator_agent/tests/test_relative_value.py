from __future__ import annotations

from datetime import date

from mercator_agent.state.models import (
    InstrumentProfile,
    PriceObservation,
)

from mercator_agent.tools.relative_value import (
    calculate_relative_value,
)


def make_price(
    instrument_id: int,
    spread: float,
    *,
    quality_score: float = 0.95,
    quality_status: str = "VALID",
) -> PriceObservation:
    return PriceObservation(
        instrument_id=instrument_id,

        clean_price=100.0,
        dirty_price=101.0,

        yield_to_maturity=0.05,
        g_spread_bps=spread,
        modified_duration=4.0,

        quality_score=quality_score,
        quality_status=quality_status,

        curve_version=2,
        reference_version=1,
    )


def make_profile(
    instrument_id: int,
    *,
    issuer: str,
    sector: str = "INDUSTRIAL",
    rating: str = "BBB",
    maturity_year: int = 2036,
) -> InstrumentProfile:
    return InstrumentProfile(
        instrument_id=instrument_id,
        instrument_type="CORPORATE_BOND",
        issuer_name=issuer,

        maturity_date=date(
            maturity_year,
            6,
            15,
        ),

        rating=rating,
        sector=sector,
        currency="USD",
    )


def test_legacy_relative_value_ranking() -> None:
    results = calculate_relative_value(
        [
            make_price(1, 100.0),
            make_price(2, 150.0),
            make_price(3, 200.0),
        ]
    )

    assert len(results) == 3
    assert results[0].instrument_id == 3
    assert (
        results[0]
        .spread_difference_bps
        == 50.0
    )

    assert (
        results[-1].instrument_id
        == 1
    )


def test_peer_aware_relative_value_flags_cheap() -> None:
    prices = [
        make_price(1, 150.0),

        make_price(2, 100.0),
        make_price(3, 105.0),
        make_price(4, 110.0),
        make_price(5, 115.0),
        make_price(6, 120.0),
    ]

    profiles = [
        make_profile(
            1,
            issuer="Target Corp",
        ),

        make_profile(
            2,
            issuer="Peer A",
        ),

        make_profile(
            3,
            issuer="Peer B",
        ),

        make_profile(
            4,
            issuer="Peer C",
        ),

        make_profile(
            5,
            issuer="Peer D",
        ),

        make_profile(
            6,
            issuer="Peer E",
        ),
    ]

    results = calculate_relative_value(
        prices,
        profiles=profiles,
        target_instrument_ids=[1],
    )

    assert len(results) == 1

    result = results[0]

    assert result.instrument_id == 1
    assert result.peer_count == 5

    assert (
        result.peer_median_spread_bps
        == 110.0
    )

    assert (
        result.spread_difference_bps
        == 40.0
    )

    assert result.spread_z_score is not None
    assert result.spread_z_score > 1.0

    assert result.classification == "CHEAP"
    assert result.confidence == "MEDIUM"


def test_peer_filter_rejects_sector_mismatch() -> None:
    prices = [
        make_price(1, 150.0),
        make_price(2, 100.0),
        make_price(3, 105.0),
        make_price(4, 110.0),
    ]

    profiles = [
        make_profile(
            1,
            issuer="Target",
        ),

        make_profile(
            2,
            issuer="Industrial A",
        ),

        make_profile(
            3,
            issuer="Industrial B",
        ),

        make_profile(
            4,
            issuer="Bank Peer",
            sector="FINANCIAL",
        ),
    ]

    results = calculate_relative_value(
        prices,
        profiles=profiles,
        target_instrument_ids=[1],
    )

    assert len(results) == 1

    assert set(
        results[0].peer_instrument_ids
    ) == {2, 3}


def test_peer_filter_rejects_distant_rating() -> None:
    prices = [
        make_price(1, 150.0),
        make_price(2, 100.0),
        make_price(3, 105.0),
        make_price(4, 250.0),
    ]

    profiles = [
        make_profile(
            1,
            issuer="Target",
            rating="BBB",
        ),

        make_profile(
            2,
            issuer="Peer A",
            rating="BBB+",
        ),

        make_profile(
            3,
            issuer="Peer B",
            rating="BBB-",
        ),

        make_profile(
            4,
            issuer="Distressed",
            rating="B",
        ),
    ]

    results = calculate_relative_value(
        prices,
        profiles=profiles,
        target_instrument_ids=[1],
    )

    assert len(results) == 1

    assert 4 not in (
        results[0]
        .peer_instrument_ids
    )


def test_peer_filter_rejects_distant_maturity() -> None:
    prices = [
        make_price(1, 150.0),
        make_price(2, 100.0),
        make_price(3, 105.0),
        make_price(4, 120.0),
    ]

    profiles = [
        make_profile(
            1,
            issuer="Target",
            maturity_year=2036,
        ),

        make_profile(
            2,
            issuer="Peer A",
            maturity_year=2035,
        ),

        make_profile(
            3,
            issuer="Peer B",
            maturity_year=2037,
        ),

        make_profile(
            4,
            issuer="Long Peer",
            maturity_year=2045,
        ),
    ]

    results = calculate_relative_value(
        prices,
        profiles=profiles,
        target_instrument_ids=[1],
    )

    assert len(results) == 1

    assert 4 not in (
        results[0]
        .peer_instrument_ids
    )


def test_invalid_market_data_is_excluded() -> None:
    results = calculate_relative_value(
        [
            make_price(1, 150.0),

            make_price(
                2,
                100.0,
                quality_status=
                    "LOW_CONFIDENCE",
            ),
        ]
    )

    assert results == []


def test_same_issuer_is_excluded_when_external_peers_exist() -> None:
    prices = [
        make_price(1, 150.0),
        make_price(2, 145.0),
        make_price(3, 100.0),
        make_price(4, 105.0),
        make_price(5, 110.0),
    ]

    profiles = [
        make_profile(
            1,
            issuer="Target",
        ),

        make_profile(
            2,
            issuer="Target",
        ),

        make_profile(
            3,
            issuer="Peer A",
        ),

        make_profile(
            4,
            issuer="Peer B",
        ),

        make_profile(
            5,
            issuer="Peer C",
        ),
    ]

    result = calculate_relative_value(
        prices,
        profiles=profiles,
        target_instrument_ids=[1],
    )[0]

    assert 2 not in (
        result.peer_instrument_ids
    )


def test_zero_dispersion_does_not_create_infinite_z_score() -> None:
    prices = [
        make_price(1, 130.0),
        make_price(2, 100.0),
        make_price(3, 100.0),
        make_price(4, 100.0),
    ]

    profiles = [
        make_profile(
            1,
            issuer="Target",
        ),

        make_profile(
            2,
            issuer="Peer A",
        ),

        make_profile(
            3,
            issuer="Peer B",
        ),

        make_profile(
            4,
            issuer="Peer C",
        ),
    ]

    result = calculate_relative_value(
        prices,
        profiles=profiles,
        target_instrument_ids=[1],
    )[0]

    assert (
        result.spread_z_score
        is None
    )

    assert (
        result.classification
        == "CHEAP"
    )
