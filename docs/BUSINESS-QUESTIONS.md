# How each business question is answered

The brief lists seven questions ACME cannot answer today. Each one maps to a
specific screen and a specific API endpoint. Use this table when you present.

| # | Question | Where to see it | API endpoint |
|---|---|---|---|
| 1 | What is the current status of each active project? | Projects list | `GET /api/projects?status=active` |
| 2 | Which projects are at risk of missing their deadlines? | Dashboard, top table | `GET /api/analytics/at-risk` |
| 3 | How are resources allocated across projects? | People page | `GET /api/analytics/resource-utilisation` |
| 4 | What are the key deliverables and their completion status? | Project → Deliverables tab | `GET /api/deliverables?project_id=1` |
| 5 | Which team members are over-allocated across multiple projects? | Dashboard, lower panel | `GET /api/analytics/over-allocated` |
| 6 | What is the dependency chain between deliverables? | Project → Dependency chain tab | `GET /api/projects/1/dependency-chain` |
| 7 | How much budget has been consumed versus planned? | Budget page | `GET /api/analytics/budget` |

---

## The risk model, in plain words

`backend/app/services.py` runs six checks against every open project:

1. The end date has passed and the project is not marked complete.
2. Schedule used exceeds work delivered by 20 percentage points or more.
3. 90% or more of the budget is gone while less than 75% is delivered.
4. At least one deliverable is marked blocked.
5. One or more deliverables are past their due date and unfinished.
6. The project is on hold.

**One check firing → "watch". Two or more → "at risk".**

The reasons are returned alongside the verdict, so the dashboard shows *why*
something is flagged rather than just showing a red dot. That is the difference
between a status report and a useful tool.

---

## The over-allocation model

Each assignment records what share of a person's week a project takes. Add up
every assignment on a live project (planning, active or on hold — completed and
cancelled projects release their people). Anything over 100% means that person
is promised to more work than there are hours in their week.

Capacity is stored per person in hours, so a part-time colleague on 32 hours is
correctly treated as full at 100%, not at 40 hours' worth of work.

---

## The dependency chain

Each deliverable can point at one predecessor via `depends_on_id`. The API
walks that structure into an ordered, depth-tagged list, so the UI can indent
each item under the thing it waits on.

A deliverable is marked **waiting on predecessor** when the item it depends on
is not yet complete. That is how you find the true bottleneck: look for the
earliest incomplete item with a long tail indented beneath it.

The walk also guards against circular references — anything not reached by the
walk is appended at the end rather than looping forever.
