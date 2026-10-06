from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from .service import BridgeService

mcp = MCPServer("bridge-llm")


def _run(payload: dict[str, Any]) -> dict[str, Any]:
    return BridgeService().run(payload)


@mcp.tool()
def bridge_run(payload: dict[str, Any]) -> dict[str, Any]:
    """Run any bridge-llm JSON action."""
    return _run(payload)


@mcp.tool()
def recommend_bid(
    hand: str,
    seat: str,
    dealer: str,
    vulnerability: str = "NONE",
    auction: list[str] | None = None,
    scoring: str = "IMPS",
    details: bool = True,
) -> dict[str, Any]:
    """Ask BEN for a bid recommendation."""
    return _run({
        "action": "bid", "hand": hand, "seat": seat, "dealer": dealer,
        "vulnerability": vulnerability, "auction": auction or [],
        "scoring": scoring, "details": details,
    })


@mcp.tool()
def recommend_lead(
    hand: str,
    seat: str,
    dealer: str,
    auction: list[str],
    vulnerability: str = "NONE",
    scoring: str = "IMPS",
    details: bool = True,
) -> dict[str, Any]:
    """Ask BEN for an opening-lead recommendation."""
    return _run({
        "action": "lead", "hand": hand, "seat": seat, "dealer": dealer,
        "vulnerability": vulnerability, "auction": auction,
        "scoring": scoring, "details": details,
    })


@mcp.tool()
def recommend_play(
    hands: dict[str, str],
    seat: str,
    dealer: str,
    auction: list[str],
    played: list[str],
    vulnerability: str = "NONE",
    scoring: str = "IMPS",
    details: bool = True,
) -> dict[str, Any]:
    """Ask BEN for the next card using normal hidden-information play."""
    return _run({
        "action": "play", "hands": hands, "seat": seat, "dealer": dealer,
        "vulnerability": vulnerability, "auction": auction, "played": played,
        "scoring": scoring, "details": details,
    })


@mcp.tool()
def double_dummy_table(
    deal: dict[str, str], vulnerability: str = "NONE"
) -> dict[str, Any]:
    """Use DDS3 to calculate makeable tricks for all seats/strains plus par."""
    return _run({"action": "dd_table", "deal": deal, "vulnerability": vulnerability})


@mcp.tool()
def double_dummy_best_card(
    deal: dict[str, str],
    dealer: str,
    auction: list[str],
    played: list[str] | None = None,
) -> dict[str, Any]:
    """Use full-information DDS3 to rank legal cards at the current position."""
    return _run({
        "action": "dd_best_card", "deal": deal, "dealer": dealer,
        "auction": auction, "played": played or [],
    })


@mcp.tool()
def double_dummy_analyse_play(
    deal: dict[str, str], dealer: str, auction: list[str], played: list[str]
) -> dict[str, Any]:
    """Use DDS3 to analyze trick-count changes through a play sequence."""
    return _run({
        "action": "dd_analyse_play", "deal": deal, "dealer": dealer,
        "auction": auction, "played": played,
    })


@mcp.tool()
def bridge_status() -> dict[str, Any]:
    """Check whether BEN REST API and DDS3 are available."""
    return _run({"action": "status"})


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
