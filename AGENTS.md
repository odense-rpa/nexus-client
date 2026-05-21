# Nexus Client

Read these first when inspecting this repo:

- `README.md`
- `docs/nexus.md`
- `tests/`

Use `uv` for Python commands.

## Boundaries

- `kmd_nexus_client/` is only the Nexus client library. Keep CURA config, CURA types, and robot orchestration out of it.
- Hide reusable Nexus mechanics that are noisy in robot code: HATEOAS link traversal, endpoint names, exact-search fallbacks, response-shape checks, and HTTP status handling.
- Expose reusable operations in Nexus terms, not robot process terms. `find_borger_by_cpr` is appropriate; `process_apv_order` is not.
- Prefer small stable values for fields robots repeatedly depend on, such as `NexusBorger`. Keep raw dictionaries for operations that need unresolved Nexus links or where the API shape is still being explored.
- Do not leak robot-specific APV rules into this client. If a behavior would help multiple robots, add it here; if it is a process decision for one robot, keep it in that robot.

## HCL Depot

- Keep HCL depot mechanics in `kmd_nexus_client.functionality.hcl_depot`: HMI search, depot stock item selection, current basket actions, delivery metadata, request readiness polling, finalize, and best-effort cleanup.
- The basket `finalize` action should reuse Nexus' action prototype. Do not set `orderedDate` to a plain date string; Nexus expects a `LocalDateTime` there and the GUI/API prototype leaves it null while `requestedDeliveryDate` carries the delivery date.
- HCL request reservation can be asynchronous. Poll the basket request until pending statuses clear before finalizing.
