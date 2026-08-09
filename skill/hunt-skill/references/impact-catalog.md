# Protocol-Specific Impact Catalog

An impact catalog is not a vulnerability checklist. It is a set of concrete bad states for this protocol, each tied to an invariant and the exact decision that could be tricked.

## Construction Formula

For every impact row, complete all fields:

```text
protocol archetype + protocol-specific mechanism
-> protected invariant
-> exact decision point
-> attacker-created bad state
-> later consumer/action
-> meaningful impact
```

Use multiple archetypes for hybrid systems. A vault using lending collateral needs both vault and lending impacts; a bridge-wrapped vault also needs bridge impacts.

## Protocol Case Requirements

Do not mark an impact `READY` until it names:

1. The protocol's concrete assets, shares, debt, rights, or lifecycle state.
2. The functions/modules that make the critical decision.
3. The data that decision treats as authoritative.
4. At least one permissionless flow that can shape that data.
5. The later flow that realizes loss, theft, insolvency, or meaningful denial of service.

Generic wording such as "share price can be manipulated" remains `DRAFT`.

## Vault Example

Generic seed:

```text
Invariant: share issuance and redemption preserve proportional ownership.
Impact: exchange-rate manipulation.
```

Protocol-specific Grunt-style case:

```text
Invariant:
  Facility/vault shares must represent the same economic assets used by claim,
  cancellation, and debt settlement paths.

Decision point:
  The mint/redeem/claim path converts between shares, principal, and live or
  cached facility accounting.

Bad state:
  A permissionless request, donation, cancellation, external strategy action,
  or delayed checkpoint moves one representation without its coupled value.

Attacker goal:
  Enter or exit while the favorable representation is authoritative, leaving
  other holders or the protocol with the loss.

Flows to inspect:
  request -> fulfill/cancel -> debt update -> claim/redeem -> later settlement.
```

This example is a hunt target, not a claim that Grunt is vulnerable.

## Backward Impact Questions

Start with a concrete attacker objective:

- Prevent liquidation of my unsafe position.
- Redeem before a loss is recognized.
- Mint shares against value the vault cannot realize.
- Make another user's required exit revert indefinitely.
- Cause a destination chain to release value without final source backing.

Then ask in layers:

1. Which final check or state authorizes the desired outcome?
2. Which variables feed that decision?
3. Which functions and integrations can alter those variables?
4. Which are permissionless, orderable, flash-capitalized, delayed, or externally manipulable?
5. Can the bad state survive until the final consumer?

## Seed And Refine

`impact-seed` creates `DRAFT` rows from `assets/impact-catalogs.json`. Refine each promising row with `impact-upsert` and mark it `READY` only when all protocol fields are concrete. Add custom impacts whenever specifications or architecture expose a bad state absent from the templates.
