# Linkage Methodology

## Purpose

Pre-2004 malpractice records do not provide the same total-payment structure as post-2004 records. Any attempt to reconstruct total claim payment must therefore rely on a transparent and defensible linkage rule rather than a loose practitioner-level aggregation.

## Working Unit

The notebook does not assume a true claim ID exists in the public-use file. It constructs a `derived payment episode` as a temporary analytical unit.

## Linkage Tiers

### Tier 1: Strict

Uses:

- `PRACTNUM`
- `STATE`
- `MALYEAR1`
- `MALYEAR2`
- `ALGNNATR`
- `PAYTYPE`

This is the preferred reconstruction rule.

### Tier 2: Moderate

Uses:

- `PRACTNUM`
- `STATE`
- `MALYEAR1`
- `ALGNNATR`
- `ORIGYEAR_WINDOW`

This is only acceptable if validation is still strong.

### Tier 3: Exploratory

Uses:

- `PRACTNUM`
- `STATE`
- `MALYEAR1`

This tier is for sensitivity testing only and should not be treated as publishable reconstruction unless validation is unexpectedly strong.

## Ambiguity Rules

An episode is flagged as ambiguous if any of the following occur inside the derived cluster:

- more than one practitioner appears
- more than one state appears
- more than one allegation group appears
- more than one payment type appears
- the report-year span is wider than the tier allows

Ambiguous clusters are excluded from reconstruction.

## Validation Rule

The linkage tier must be tested on post-2004 records first, where `TOTALPMT` is observed. The notebook compares:

- grouped `sum(PAYMENT_ADJ)`
- observed `TOTALPMT_ADJ`

Key validation outputs:

- median absolute percent error
- mean absolute percent error
- share within 10%
- share within 25%
- ambiguous share

## Decision Rule

Use reconstructed totals only if:

- the linkage rule is deterministic and explainable
- validation metrics are acceptable
- ambiguous-share remains low enough to keep results stable

If not, keep pre-2004 analysis at the report level and restrict total-payment analysis to observed post-2004 totals.

## Reporting Rule

Every output using total payments must distinguish:

- `observed`
- `reconstructed`
- `unresolved`

