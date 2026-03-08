---
trigger: manual
---
# Frontend Styling Guidelines (High Level)

## Goal
Create a **sleek, modern, executive-friendly** demo UI that is fast to understand: **Input → Decide Offer → Result**.

## Design principles
- **Clarity over density:** minimal text, obvious primary action.
- **Polished, not flashy:** clean spacing, subtle shadows, restrained accents.
- **Consistent hierarchy:** clear page title, section headers, and primary CTA.
- **Responsive by default:** works well on laptop screen and when window is resized.

## Layout
- Single-page layout with a centered container.
- Two main panels:
  1) **Subscriber Inputs** (form)
  2) **Decision Output** (results card)
- Keep the primary action button (“Decide Offer”) prominent and above the fold.
- Include a small row of **Scenario buttons** at the top of the form.

## Typography & spacing
- Use **2–3 font sizes** max (title, body, small labels).
- Prefer generous whitespace: consistent padding and gaps.
- Align labels and inputs cleanly; avoid clutter.

## Components
- Use card-style containers with subtle borders/shadows.
- Inputs:
  - clear labels
  - helpful placeholders
  - inline validation for required fields / churn risk 0–1
- Buttons:
  - one primary button
  - scenario buttons as secondary/ghost buttons

## Result presentation
- Highlight:
  - **Offer name** (most prominent)
  - **Discount %** (badge/pill)
  - **Explanation** (readable paragraph)
- Show raw JSON only as an optional secondary section (collapsed or smaller).

## Color & motion
- Neutral base (light background, dark text).
- One accent color for primary actions and badges.
- Use minimal motion (hover/focus states only); avoid heavy animations.

## Accessibility
- Keyboard navigable (tab order makes sense).
- Visible focus states.
- Sufficient contrast for text and buttons.

## Anti-goals
- Do not over-engineer multi-page navigation.
- Avoid dense tables, heavy dashboards, or excessive charts.
- Avoid long walls of text—keep the demo “scannable.”
