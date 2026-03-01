# CRM Schema

Use this schema in your spreadsheet or CRM system.

## Core Fields

1. `account_name`
- Protocol, fund, or partner organization.

2. `segment`
- `protocol`, `fund`, `accelerator`, `auditor`, `other`.

3. `contact_name`
- Primary commercial or technical contact.

4. `contact_role`
- Role/title (CTO, Head of Security, Founder, etc.).

5. `contact_email`
- Best working email.

6. `status`
- `open`, `won`, `lost`, `nurture`.

7. `stage`
- `lead`, `discovery`, `proposal`, `negotiation`, `closed`.

8. `deal_type`
- `sprint`, `retainer`, `subscription`, `partner`.

9. `acv_usd`
- Annualized contract value estimate.

10. `probability_pct`
- Probability of close (0-100).

11. `expected_close_date`
- Date target for close.

12. `owner`
- Team owner for this account.

13. `next_action`
- Most important next step.

14. `next_action_date`
- Scheduled date of next action.

15. `last_touch_date`
- Last outbound/inbound contact date.

16. `notes`
- Key context and blockers.

## Stage Exit Criteria

1. `lead -> discovery`
- Qualified need, identified stakeholder, and meeting booked.

2. `discovery -> proposal`
- Problem validated and budget/timeline confirmed.

3. `proposal -> negotiation`
- Scope accepted with legal/commercial edits pending.

4. `negotiation -> closed`
- Signed agreement and kickoff date set.
