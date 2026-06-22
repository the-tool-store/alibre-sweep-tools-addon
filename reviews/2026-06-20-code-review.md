# alibre-sweep-tools-addon — Code Review (Correctness)

**Date:** 2026-06-20
**Scope:** Second-opinion review, code only (correctness bugs). Reviewed the addon's own source: `PipeTool.py`, `alibre_setup.py`, `Template.py`. The `submodules/alibre-script-adk/` tree is a third-party dependency and was treated as out of scope.

**Summary: 4 bugs — 1 High, 2 Medium, 1 Low**

## High

**`source/PipeTool.py:68 & :77` — Inconsistent circle radius vs. wall-thickness math produces a wrong hollow wall.**
The outer circle uses the input directly as the radius (`OuterSize = ProfileSize; AddCircle(0,0,OuterSize,...)`), but the inner circle is computed as `InnerSize = ProfileSize - (Thickness * 2)`. With `ProfileSize` interpreted as a *radius*, the correct inner radius is `ProfileSize - Thickness`; subtracting `2*Thickness` gives a wall twice as thick as requested. (Compare `Template.py:641/649`, which correctly uses `ProfileSize/2.0` for the radius and `(ProfileSize/2.0) - Thickness` for the inner radius.) The square branch (`:70`/`:79`) treats `ProfileSize` as full width, so within one script "Size" means radius for circles but width for squares — the two profile types are not equivalent for the same input.

## Medium

**`source/PipeTool.py:74` — Hollow guard uses the wrong bound for circles, silently dropping the inner loop.**
The guard is `if IsHollow and Thickness > 0 and Thickness < (ProfileSize / 2.0)`. Since the circle's outer radius is `ProfileSize` (not `ProfileSize/2`), a valid thickness up to `ProfileSize` should be allowed; values between `ProfileSize/2` and `ProfileSize` silently skip the inner circle and produce a solid sweep with no error message, contradicting the user's "Hollow" request.

**`source/PipeTool.py:42-43` (and the 2D branch `:45-46`) — Degenerate direction vector for closed/looped path splines.**
The profile-plane normal is derived from two spline samples at parameters `0.0` and `0.001`. For a closed spline, or any spline whose start tangent is near-zero over that tiny interval, `DirectionVector` (line 59) can be ~zero, and `AddPlane('SweepProfilePlane', DirectionVector, StartPoint3D)` will fail or create a malformed plane. There is no validation that `DirectionVector` is non-zero (unlike `Template.py`, which at least wraps creation in error handling/rollback). This is an unhandled edge case that aborts the script with an opaque API error.

## Low

**`source/SweepTools/src/scripts/Template.py:635` — Inner-rectangle sizing/positioning when the profile center is not the origin.**
For the hollow rectangle, the inner half-extent is `inner_h = (ProfileSize / 2.0) - Thickness`, drawn at `cx ± inner_h`; the outer uses `half = ProfileSize/2.0` at `cx ± half`. That part is consistent (uniform wall). However `pt2d = created_sketch.GlobaltoPoint(sp[0], sp[1], sp[2])` uses the path's *start point* as the profile center on the profile plane; if `GlobaltoPoint` returns the projected origin offset, the profile may not be centered on the path. This depends on Alibre API semantics and is plausibly correct, so flagged only as Low/uncertain.

## Notes (not bugs)

- All three reviewed files are IronPython 2 (`print` statements), which is correct for the Alibre Script runtime — not a defect.
- `alibre_setup.py` correctly guards `CurrentSession` with `if CurrentSession and isinstance(...)`; no issue.
- `Template.py`'s build/rollback logic is sound; the broad `except: pass` blocks swallow errors but are intentional cleanup guards, not correctness bugs.

The single most important fix is the **High** finding: the inner-circle radius formula in `PipeTool.py` produces a wall twice the requested thickness due to mixing radius and diameter conventions.

---

## Fixes applied — 2026-06-20

- **[High] `source/PipeTool.py`** — inner-circle radius `ProfileSize - (Thickness * 2)` → `ProfileSize - Thickness` (wall thickness now equals `Thickness`); hollow guard bound corrected to `Thickness < ProfileSize`.
- **[Medium] `source/PipeTool.py`** — the spline start-tangent is now sampled over progressively larger deltas (`0.001, 0.01, 0.1, 0.25`) until a non-zero `DirectionVector` is found; if still degenerate (`< 1e-9`), the script prints a clear message and aborts gracefully before `AddPlane`.
- **[Low] `SweepTools/src/scripts/Template.py:635`** — reviewed and confirmed correct (the `GlobaltoPoint` centering is the intended, plane-origin-safe behavior); left unchanged.

*Caveat: changes applied to source; not verified by build.*
