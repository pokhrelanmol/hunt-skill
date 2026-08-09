# CHAT Workflow

## Phase 1: Frame The Question

**Entry:** The user asks a question, expresses confusion, proposes an attack, or says continue.

1. Answer the actual question first.
2. Translate uncertainty into one precise security question.
3. Load only directly relevant active IDs and bounded graph context.

**Exit:** The claim, protected invariant, and missing fact are explicit.

## Phase 2: Stress-Test

**Entry:** A concrete question or idea exists.

1. Trace the shortest relevant state journey.
2. Test the strongest blocker or safe explanation.
3. Connect the idea to a protocol-specific impact goal only if the chain is concrete.
4. Do not launch broad scans or proof work.

**Exit:** Return `Fact`, `Question`, `Lead`, `Primitive`, `Chain`, `Blocked`, or `Rejected` with one next discriminating check.

## Phase 3: Persist Selectively

**Entry:** The exchange produced reusable protocol knowledge, a lead, or kill evidence.

1. Update the relevant SQLite record.
2. Update compact Markdown only when active focus changed.

**Exit:** Future continuation can retrieve the result by ID.
