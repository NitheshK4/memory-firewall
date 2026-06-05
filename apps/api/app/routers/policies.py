from fastapi import APIRouter

from apps.api.app.models.policy import PolicyAction, PolicyRule, PolicyScope

router = APIRouter(prefix="/policies", tags=["policies"])

# ---------------------------------------------------------------------------
# In-memory rule store (swap for DB-backed store in production)
# ---------------------------------------------------------------------------
_RULES: dict[str, PolicyRule] = {
    "default-block-credentials": PolicyRule(
        rule_id="default-block-credentials",
        name="Block credential requests",
        description="Any memory flagged with credential_request is blocked unconditionally.",
        scope=PolicyScope.GLOBAL,
        condition_flags=["credential_request"],
        action=PolicyAction.BLOCK,
        priority=10,
    ),
    "default-quarantine-external": PolicyRule(
        rule_id="default-quarantine-external",
        name="Quarantine high-risk external input",
        description="Long-form external content with risk >= 0.58 is quarantined.",
        scope=PolicyScope.SOURCE_TYPE,
        scope_value="email",
        condition_flags=["external_longform_input"],
        min_risk_score=0.58,
        action=PolicyAction.QUARANTINE,
        priority=50,
    ),
}


@router.get("/", summary="List all policy rules")
def list_policies() -> list[PolicyRule]:
    return list(_RULES.values())


@router.get("/{rule_id}", summary="Get a policy rule by ID")
def get_policy(rule_id: str) -> PolicyRule:
    from fastapi import HTTPException

    rule = _RULES.get(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    return rule


@router.post("/", summary="Create a new policy rule", status_code=201)
def create_policy(rule: PolicyRule) -> PolicyRule:
    _RULES[rule.rule_id] = rule
    return rule


@router.delete("/{rule_id}", summary="Delete a policy rule", status_code=204)
def delete_policy(rule_id: str) -> None:
    from fastapi import HTTPException

    if rule_id not in _RULES:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    del _RULES[rule_id]
