"""Memory Firewall CLI tool (mfw)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from apps.api.app.models.provenance import ProvenanceRecord
from apps.api.app.services.claim_extractor import ClaimExtractor
from apps.api.app.services.policy_engine import PolicyEngine
from apps.api.app.services.risk_service import RiskService
from packages.client import MemoryFirewallClient, MemoryFirewallClientError


def cmd_check_local(args: argparse.Namespace) -> int:
    """Evaluate text offline through the local RiskService & PolicyEngine."""
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            print(f"Error reading file {args.file}: {exc}", file=sys.stderr)
            return 1
    else:
        content = args.text or ""

    if not content.strip():
        print("Error: content cannot be empty", file=sys.stderr)
        return 1

    extractor = ClaimExtractor()
    risk_service = RiskService()
    policy_engine = PolicyEngine()

    claims = extractor.extract(content)
    prov = ProvenanceRecord(
        source_type=args.source_type,
        source_id="cli_check",
        actor=args.actor,
        authority_score=args.authority,
    )
    assessment = risk_service.assess(claims=claims, provenance=prov, contradictions=[], content=content)
    verdict = policy_engine.decide(assessment=assessment, provenance=prov, content=content)

    result = {
        "content_length": len(content),
        "action": verdict.action.value,
        "trust_score": round(verdict.trust_score, 3),
        "risk_score": round(assessment.score, 3),
        "flags": assessment.flags,
        "reasons": verdict.reasons,
        "claims_count": len(claims),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status_color = (
            "\033[92mALLOW\033[0m"
            if verdict.action.value == "allow"
            else "\033[93m" + verdict.action.value.upper() + "\033[0m"
            if verdict.action.value == "quarantine"
            else "\033[91m" + verdict.action.value.upper() + "\033[0m"
        )
        print(f"\n--- Memory Firewall Check ---")
        print(f"Verdict:     {status_color}")
        print(f"Trust Score: {verdict.trust_score:.2f}")
        print(f"Risk Score:  {assessment.score:.2f}")
        print(f"Flags:       {', '.join(assessment.flags) if assessment.flags else 'none'}")
        if verdict.reasons:
            print(f"Reasons:")
            for r in verdict.reasons:
                print(f"  - {r}")
        print()
    return 0 if verdict.action.value == "allow" else 2


def cmd_health(args: argparse.Namespace) -> int:
    """Check the health of a remote or local Memory Firewall API server."""
    client = MemoryFirewallClient(base_url=args.url)
    try:
        res = client.health(detailed=args.detailed)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Status:  {res.get('status')}")
            print(f"Version: {res.get('version', 'unknown')}")
            if "components" in res:
                print("Components:")
                for k, v in res["components"].items():
                    print(f"  - {k}: {v}")
        return 0
    except MemoryFirewallClientError as exc:
        print(f"Health check failed: {exc}", file=sys.stderr)
        return 1


def cmd_audit_stats(args: argparse.Namespace) -> int:
    """Query audit event statistics."""
    client = MemoryFirewallClient(base_url=args.url)
    try:
        stats = client.get_audit_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("\n--- Audit Log Event Counts ---")
            for event_type, count in stats.items():
                print(f"  {event_type:<25} : {count}")
            print()
        return 0
    except MemoryFirewallClientError as exc:
        print(f"Failed to fetch audit stats: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mfw",
        description="Memory Firewall Command-Line Interface (mfw)",
    )
    parser.add_argument("--version", action="version", version="mfw 0.2.0")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # check subcommand
    check_p = subparsers.add_parser("check", help="Evaluate text or file against firewall policies locally")
    check_p.add_argument("text", nargs="?", help="Text to check")
    check_p.add_argument("-f", "--file", help="Path to file to check")
    check_p.add_argument("--source-type", default="user", help="Source type (user, web, email, agent)")
    check_p.add_argument("--actor", default="cli_user", help="Actor identifier")
    check_p.add_argument("--authority", type=float, default=0.7, help="Authority score [0.0 - 1.0]")
    check_p.add_argument("--json", action="store_true", help="Output raw JSON")
    check_p.set_defaults(func=cmd_check_local)

    # health subcommand
    health_p = subparsers.add_parser("health", help="Check Memory Firewall API health")
    health_p.add_argument("--url", default="http://localhost:8000", help="Memory Firewall API base URL")
    health_p.add_argument("--detailed", action="store_true", help="Fetch detailed component health")
    health_p.add_argument("--json", action="store_true", help="Output raw JSON")
    health_p.set_defaults(func=cmd_health)

    # audit subcommand
    audit_p = subparsers.add_parser("audit", help="Audit log operations")
    audit_sub = audit_p.add_subparsers(dest="audit_command", help="Audit subcommands")
    audit_stats_p = audit_sub.add_parser("stats", help="Show event distribution in audit log")
    audit_stats_p.add_argument("--url", default="http://localhost:8000", help="API base URL")
    audit_stats_p.add_argument("--json", action="store_true", help="Output raw JSON")
    audit_stats_p.set_defaults(func=cmd_audit_stats)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
