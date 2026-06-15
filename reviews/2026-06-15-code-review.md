# Code Review — alibre-sweep-tools-addon

- **Date:** 2026-06-15
- **Branch:** `review/2026-06-15-code-review` (branched from `the-tool-store` @ `ea43b48` — "cleanup push")
- **Reviewer:** Claude (Opus 4.8)
- **Scope:** Full repository review (VB.NET add-on host + IronPython sweep-tool scripts + project/solution files + repo hygiene)

---

## 1. Summary

This is an Alibre Design add-on that adds a "Sweep Tools" ribbon menu with a single command,
"Advanced Sweep Tool". The VB.NET layer (`AlibreAddOn.vb`) is the COM-facing host that registers
the menu and uses an embedded IronPython 2.7 engine to run a script. The Python layer
(`scripts/Template.py`) presents a WinForms dialog and builds a swept solid/hollow profile along a
selected sketch path; `scripts/alibre_setup.py` is a small bootstrap meant to hand the host's
session to the script.

Compared to the sibling `alibre-shapes-addon`, this repo is **leaner and cleaner in some respects**
(no committed `.exe`, a real `.gitignore`, no `src\` vs `source\` build-path mismatch) but **worse
in others**: there is **no build/installer tooling at all** despite the README describing a build
flow, the **running script ignores the session the host injects** (and re-grabs `TopmostSession`),
the bootstrap script's work is therefore dead, there is a **null-session dereference** on the
command path, and a **second, divergent copy of the tool (`PipeTool.py`) is orphaned at the repo
root**. Paths remain **hard-coded to one exact Alibre version**.

**Overall:** Functional prototype. The dialog code in `Template.py` is genuinely careful (lots of
defensive `try/except`, feature-rollback on failure). The host plumbing has a real correctness bug
(null session) and an architectural one (injected session unused). No packaging exists yet.

### Findings by severity

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 3 |
| Medium   | 5 |
| Low / Nit| 7 |

---

## 2. Critical

None. The build (`SweepTools.vbproj`) is internally consistent and the running script's content
files are all copied to output, so unlike the sibling repo there is no build-breakage or
missing-content Critical.

---

## 3. High

### H-1. The running script ignores the host-injected session and re-acquires `TopmostSession`
**Files:** [Template.py:35-41](source/SweepTools/src/scripts/Template.py), [Template.py:84-86](source/SweepTools/src/scripts/Template.py), [alibre_setup.py:7-11](source/SweepTools/src/scripts/alibre_setup.py), [AlibreAddOn.vb:111](source/SweepTools/src/AlibreAddOn.vb)

`AlibreAddOn.vb` carefully resolves the invoked session and injects it into the Python scope, and
`alibre_setup.py` turns it into `CurrentPart`/`CurrentAssembly`:

```vb
scope.SetVariable("CurrentSession", session)   ' AlibreAddOn.vb:111
```
```python
# alibre_setup.py
if CurrentSession and isinstance(CurrentSession, AlibreX.IADPartSession):
    CurrentPart = Part(CurrentSession)
```

But `Template.py` throws all of that away and reconnects to whatever Alibre considers topmost:

```python
alibre = Marshal.GetActiveObject("AlibreX.AutomationHook")   # Template.py:35
root = alibre.Root
...
MyPart = Part(root.TopmostSession)                            # Template.py:41
```

and the selection list box does the same (`AlibreScript.API.Global.Root` → `TopmostSession`,
[Template.py:84-86](source/SweepTools/src/scripts/Template.py)). `TopmostSession` is not guaranteed
to be the document the menu command was invoked on, so geometry can be created in the wrong part.
It also makes the entire host→script session-passing pipeline (the most important thing the C#/VB
layer does) **dead code**. Use the injected `CurrentPart` from `alibre_setup.py` instead of
re-acquiring the session.

### H-2. Null-session dereference on the command path
**File:** [AlibreAddOn.vb:48-75](source/SweepTools/src/AlibreAddOn.vb), [AlibreAddOn.vb:108](source/SweepTools/src/AlibreAddOn.vb)

`InvokeCommand` builds `session` by matching the identifier, then falling back to "first session":

```vb
If session Is Nothing Then
    For Each s As IADSession In _AlibreRoot.Sessions
        session = s
        Exit For
    Next
End If
```

If `_AlibreRoot.Sessions` is empty (no open document, or the collection enumeration throws and is
swallowed by the bare `Catch` at line 67), `session` stays `Nothing`. It is then passed straight
into `ExecuteScript`, where the first use is:

```vb
scope.SetVariable("SessionIdentifier", session.Identifier)   ' AlibreAddOn.vb:108
```

`session.Identifier` on `Nothing` throws a `NullReferenceException`. It is caught by the outer
handler and shown as a generic error, but it should be guarded explicitly with a clear
"Open a part first" message before running the script. (The `<Workspace type="Always"/>` in the
`.adc` means the menu is enabled even with no document open, so this path is reachable.)

### H-3. Hard-coded, version-pinned Alibre install paths
**Files:** [SweepTools.vbproj:41,45,49](source/SweepTools/src/SweepTools.vbproj), [launchSettings.json:8](source/SweepTools/src/My%20Project/launchSettings.json)

```xml
<HintPath>C:\Program Files\Alibre Design 28.1.1.28227\Program\AlibreAddOn.dll</HintPath>
<HintPath>C:\Program Files\Alibre Design 28.1.1.28227\Program\Addons\AlibreScript\AlibreScriptAddOn.dll</HintPath>
<HintPath>C:\Program Files\Alibre Design 28.1.1.28227\Program\AlibreX.dll</HintPath>
```
```json
"executablePath": "C:\\Program Files\\Alibre Design 28.1.1.28227\\Program\\Alibre Design.exe"
```

These break on any other Alibre version or non-default install location, so the project will not
restore/build on another machine without hand-editing. Introduce an `AlibreInstallDir` MSBuild
property (overridable via env var, with the registry key `SOFTWARE\Alibre, LLC\Alibre Design` or a
discovered path as fallback) and reference it from every `HintPath`.

**Good news:** the *runtime* search-path resolution already does this correctly —
[AlibreAddOn.vb:88](source/SweepTools/src/AlibreAddOn.vb) derives the install root from the loaded
`AlibreX.dll` location rather than hard-coding it. Only the build-time references are pinned.

---

## 4. Medium

### M-1. `PipeTool.py` is an orphaned, divergent copy of the tool
**File:** [PipeTool.py:1-89](source/PipeTool.py)

A second implementation of the sweep tool sits at the repo root. It is **not** copied to output (no
`<Content>` entry), **not** referenced by `AlibreAddOn.vb`, and **not** wired into the `.adc`, so it
never runs. It is also an older/cruder design that contradicts the shipping `Template.py`:

- Python 2 `print` statements ([PipeTool.py:26,90](source/PipeTool.py)) — fine under IronPython 2.7
  but inconsistent with `Template.py`, which uses `print(...)` calls.
- It calls `CurrentPart()` ([PipeTool.py:7](source/PipeTool.py)). If this script were ever run via
  `alibre_setup.py`, `CurrentPart` is a `Part` instance (or `None`), **not a callable**, so
  `CurrentPart()` would raise `TypeError`/`NoneType is not callable`. (It instead uses the
  `AlibreScript.API` global `CurrentPart()`, which only works when run inside the AlibreScript
  console — confirming this is leftover console-script code.)

The README even lists `source/PipeTool.py` as a "key source or build entry point", which is
misleading. Either promote it (and delete `Template.py`) or delete it. Right now it is pure
copy-paste confusion.

### M-2. No build or installer tooling exists, but the README claims a build flow
**Files:** [.github/README.md:31-34](.github/README.md), repository root

`git ls-files` shows no `.iss`, no `build-installer.ps1/.bat`, no `installer-config.json`, no CI
workflow under `.github/workflows/`. The README says "Open the `.sln`, restore, build from the
`source/` layout", but there is nothing that produces a registered/installable add-on (registry
keys, `.adc` placement under Alibre's `Addons` folder, etc.). For an add-on that must be installed
into Alibre to do anything, the absence of any packaging is a real gap — document the manual
install steps or add an installer.

### M-3. `SubMenuItems` returns `Nothing` for unknown ids
**File:** [AlibreAddOn.vb:123-128](source/SweepTools/src/AlibreAddOn.vb)

```vb
Public Function SubMenuItems(menuId As Integer) As Array Implements IAlibreAddOn.SubMenuItems
    If menuId = ROOT_ID Then
        Return New Integer() {CMD}
    End If
    Return Nothing
End Function
```

Returning `Nothing` (rather than `Array.Empty(Of Integer)()` / a zero-length array) across the COM
boundary can surface as an NRE in the host if it iterates the result. Return an empty array for
unknown ids.

### M-4. `My Project` is leftover WinForms-application template cruft
**Files:** [Application.myapp:3-4](source/SweepTools/src/My%20Project/Application.myapp), [launchSettings.json:3](source/SweepTools/src/My%20Project/launchSettings.json)

This is an add-on **DLL**, not an executable application, yet `Application.myapp` declares
`<MySubMain>true</MySubMain>` and `<MainForm>Form1</MainForm>` — there is no `Form1` anywhere in the
project. The `launchSettings.json` debug profile is named `"PipeTools"` (yet another stale name; the
project is `SweepTools`). None of this is fatal for a class library, but it is misleading and points
at the project having been cloned from a WinForms app template. Clean or remove `My Project`.

### M-5. `Template.py` blocks on `Marshal.GetActiveObject` with no parameterized inputs path
**File:** [Template.py:783-787](source/SweepTools/src/scripts/Template.py), [AlibreAddOn.vb:109](source/SweepTools/src/AlibreAddOn.vb)

The host injects an empty `Arguments` list (`scope.SetVariable("Arguments", New List(Of String)())`,
[AlibreAddOn.vb:109](source/SweepTools/src/AlibreAddOn.vb)) but `Template.py` never reads it — all
input comes from the modal-ish `form.Show()` (note: `Show`, not `ShowDialog`, so the form is
non-modal and the script returns immediately while the form lives on event callbacks). The
combination of (a) reconnecting via `GetActiveObject` (H-1) and (b) a non-modal form means the
lifetime of the dialog is tied to the IronPython scope/GC rather than to a blocking call; if the
scope is collected the form's timer/event handlers can be torn down unexpectedly. Confirm the form
stays alive for its full lifetime (e.g. keep a reference on a longer-lived object) or use a modal
`ShowDialog`.

---

## 5. Low / Nits

### L-1. `<None Remove="scripts\debugging.py">` references a non-existent file
[SweepTools.vbproj:18](source/SweepTools/src/SweepTools.vbproj): there is no `scripts\debugging.py`
in the repo. Stale entry — remove it.

### L-2. `Newtonsoft.Json` is referenced but never used
[SweepTools.vbproj:37](source/SweepTools/src/SweepTools.vbproj): the VB code does no JSON work.
Drop the package reference unless it is needed by something not yet committed.

### L-3. Empty `<RootNamespace>`
[SweepTools.vbproj:4](source/SweepTools/src/SweepTools.vbproj): `<RootNamespace></RootNamespace>` is
empty. Harmless (the code declares `Namespace AlibreAddOnAssembly` explicitly) but set it
intentionally or remove the empty element.

### L-4. `scale_size` ignores its `scale_factor` argument
[Template.py:61-62](source/SweepTools/src/scripts/Template.py):

```python
def scale_size(base_size, scale_factor=1.0):
    return int(base_size)
```

The second parameter is dead — the function never scales. Either implement DPI scaling or drop the
parameter to avoid implying behavior that doesn't exist.

### L-5. `printTraceBack` is a no-op
[Template.py:5-7](source/SweepTools/src/scripts/Template.py): it imports `traceback` and returns
without printing anything, yet `show_error(..., include_trace=True)` is called throughout on the
assumption it surfaces a stack trace. Real traceback info is silently lost — implement it
(`traceback.format_exc()`) or remove the `include_trace` plumbing.

### L-6. `import sys` unused in `Template.py`
[Template.py](source/SweepTools/src/scripts/Template.py): unlike `PipeTool.py`, the WinForms
`Template.py` does not `import sys` — but it does `import System` and a large WinForms surface; no
unused-import problem there. (Noted only to contrast with `PipeTool.py`, which `import sys` and uses
`sys.exit()`.) Minor.

### L-7. Errors are surfaced only via `MessageBox`, never logged
[AlibreAddOn.vb:78,102,115](source/SweepTools/src/AlibreAddOn.vb) and the Python `show_error` path
all use modal dialogs with no persistent log. For field debugging, also append to a log file so
users can report failures without screenshots.

---

## 6. What looks good

- **No committed build artifacts.** Unlike the sibling repo, there is no checked-in `.exe`/`.dll`,
  and the `.gitignore` is a full, sensible .NET ignore set (covers `bin/`, `obj/`, `*.exe`, `*.msi`,
  installer output, etc.).
- **Runtime install-path resolution is correct** ([AlibreAddOn.vb:88](source/SweepTools/src/AlibreAddOn.vb)
  derives the Alibre root from the loaded `AlibreX.dll` rather than hard-coding it).
- **Content files are actually copied to output** — `alibre_setup.py`, `Template.py`, `logo.ico`,
  and `SweepTools.adc` all have `<Content>`/`CopyToOutputDirectory` entries
  ([SweepTools.vbproj:21-34](source/SweepTools/src/SweepTools.vbproj)), so the running script's
  dependencies are present (this was a Critical in the sibling repo and is fixed here).
- **`Template.py` is genuinely defensive:** it snapshots the feature set before building, and on any
  failure rolls back the created plane/sketch/sweep ([Template.py:666-728](source/SweepTools/src/scripts/Template.py)).
  It validates units, profile size, and wall thickness (`< half the size`) before building, and
  guards 2D-vs-3D path mismatches.
- **Clean separation** between the VB host and the Python modeling/UI logic, with a single
  well-scoped menu command.
- **Lifecycle** (`AddOnLoad`/`AddOnUnload`) nulls out the module-level statics on unload.
- The `.adc` manifest is coherent and the icon plumbing (`MenuIcon` → `logo.ico`, copied to output)
  is actually wired up — better than the sibling, where icons were dead code.

---

## 7. Recommended fix order

1. **H-2** — guard the null session before `session.Identifier`; show "open a part first". (cheap,
   prevents a crash on the empty-workspace path the `.adc` explicitly allows)
2. **H-1** — make `Template.py` use the injected `CurrentPart`/`CurrentSession` instead of
   `GetActiveObject`/`TopmostSession`, so geometry lands in the right document and the host's
   session-passing stops being dead code.
3. **H-3** — parameterize the Alibre install path in the `.vbproj`/`launchSettings.json` so the
   project builds on any machine/version.
4. **M-1** — delete or promote `PipeTool.py`; remove the misleading README "entry point" line.
5. **M-2** — add (or at least document) an install/packaging path.
6. **M-3 / M-4 / M-5** — return empty arrays, strip the WinForms-app `My Project` cruft, confirm
   form lifetime.
7. Sweep the **L-*** nits (stale `debugging.py`, unused `Newtonsoft.Json`, no-op `printTraceBack`,
   dead `scale_size` arg) when touching the project file.
