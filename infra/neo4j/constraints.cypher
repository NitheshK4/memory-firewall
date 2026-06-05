// Memory Firewall – Neo4j constraints and indexes
// Run once against a fresh database via: cypher-shell -f constraints.cypher

// ── Uniqueness constraints ──────────────────────────────────────────────────
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
    FOR (m:Memory) REQUIRE m.memory_id IS UNIQUE;

CREATE INDEX source_type_idx IF NOT EXISTS FOR (s:Source) ON (s.source_type);
CREATE INDEX source_actor_idx IF NOT EXISTS FOR (s:Source) ON (s.actor);

CREATE CONSTRAINT claim_id_unique IF NOT EXISTS
    FOR (c:Claim) REQUIRE c.claim_id IS UNIQUE;



// ── Indexes for lookup performance ─────────────────────────────────────────
CREATE INDEX memory_status_idx IF NOT EXISTS FOR (m:Memory) ON (m.status);
CREATE INDEX memory_trust_idx  IF NOT EXISTS FOR (m:Memory) ON (m.trust_score);
CREATE INDEX claim_type_idx    IF NOT EXISTS FOR (c:Claim)  ON (c.claim_type);
