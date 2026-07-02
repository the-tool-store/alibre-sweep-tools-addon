# Sweep Tools for Alibre Design

Sweep Tools is an Alibre Design add-on that generates solid or hollow swept parts (pipes, tubes, and profiled members) from an existing sketch path.

You select a path sketch, pick a profile shape and size, and the add-on builds the profile plane, the profile sketch, and the sweep feature. It replaces the manual steps of constructing a profile plane and cross-section for pipe- and tube-style geometry.

The add-on is a VB.NET managed DLL for Alibre Design, developed against Alibre Design 29.0.0.29060. It targets .NET Framework 4.8.1 (`net481`, x64) and runs its dialog and sweep logic through embedded IronPython 2.7.10 scripts.

## Table Of Contents

- [What Is Here](#what-is-here)
- [Official Alibre Resources](#official-alibre-resources)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Key Files](#key-files)
- [Key Folders](#key-folders)
- [Notes](#notes)
- [License](#license)

## What Is Here

- A VB.NET add-on (`SweepTools.dll`) that registers a **Sweep Tools** menu with an **Advanced Sweep Tool** command in Alibre Design.
- An IronPython dialog (`scripts/Template.py`) that drives the workflow: path sketch selection, profile type, profile size, units, and hollow options.
- `PipeTool.py`, a standalone Alibre Script version of the same sweep built on the Alibre Script `OptionsDialog`.
- The `SweepTools.adc` manifest and `logo.ico` that Alibre uses to load and display the add-on.

Capabilities:

- Create a swept solid from any 2D or 3D path sketch in the active part.
- Choose a **circular** or **rectangular** cross-section, sized in your preferred units.
- Generate a **hollow** profile (tube/pipe) by specifying a wall thickness.
- Work in **millimeters, inches, or centimeters**, with unit labels that update in the dialog.
- Pick the path sketch from the Alibre workspace through a live selection list.
- Validate inputs and remove intermediate plane and sketch features if a sweep fails, with an option to keep the dialog open for creating multiple sweeps.

## Official Alibre Resources

Alibre's official resources for API development and AI/LLM/agent workflows: <https://www.alibre.com/api/>

## Requirements

- Alibre Design with the AlibreScript add-on installed (developed against Alibre Design 29.0.0.29060).
- .NET Framework 4.8.1 (the project targets `net481`, x64).
- IronPython 2.7.10 (pulled in as a NuGet package; runs the dialog and sweep scripts).
- Visual Studio or MSBuild with the .NET SDK-style project, plus the Alibre assemblies referenced by `SweepTools.vbproj` (`AlibreX.dll`, `AlibreAddOn.dll`, `AlibreScriptAddOn.dll`) from your Alibre install.

## Quick Start

1. Build `source/SweepTools/src/SweepTools.sln` in Release, or use the prebuilt output under `source/SweepTools/src/bin/Release/net481/`.
2. Copy the build output into a folder under your Alibre Design add-ons location and start Alibre Design.
3. Open a part that contains a path sketch, then run **Sweep Tools** > **Advanced Sweep Tool**.

## Installation

The add-on is a managed DLL described by the `SweepTools.adc` manifest, which Alibre reads to register and load it at startup.

1. Build `source/SweepTools/src/SweepTools.sln` in Release configuration, or use the prebuilt output under `source/SweepTools/src/bin/Release/net481/`.
2. Copy the build output into a folder under your Alibre Design add-ons location, including `SweepTools.dll`, `SweepTools.adc`, `logo.ico`, the `scripts/` folder, and the bundled IronPython DLLs.
3. Start Alibre Design. The Sweep Tools add-on loads at startup and appears in the add-ons menu.

## Usage

1. Open a part and create the sketch you want to use as the sweep path (a 2D or 3D sketch containing a curve).
2. From the **Sweep Tools** menu, choose **Advanced Sweep Tool** to open the dialog.
3. Click the path sketch list, then select your path sketch in the workspace. Check **Use 3D Path** if it is a 3D sketch.
4. Choose the units, profile type (Circle or Rectangle), and profile size. For a tube, enable **Create hollow profile** and set the wall thickness.
5. Click **Advanced Sweep Tool** to create the sweep. Enable **Stay open after creating** to keep the dialog open for additional sweeps.

## Key Files

| File | Purpose |
| --- | --- |
| `source/SweepTools/src/AlibreAddOn.vb` | Add-on entry point; implements `IAlibreAddOn`, registers the Sweep Tools menu and Advanced Sweep Tool command, hosts the IronPython engine, and runs `Template.py`. |
| `source/SweepTools/src/SweepTools.adc` | Alibre add-on manifest; declares the managed DLL, startup load, identifier GUID, and icon. |
| `source/SweepTools/src/SweepTools.vbproj` | VB.NET project targeting `net481` (x64) with WPF and Windows Forms, IronPython 2.7.10, and Newtonsoft.Json 13.0.3. |
| `source/SweepTools/src/SweepTools.sln` | Visual Studio solution for the project. |
| `source/SweepTools/src/scripts/Template.py` | IronPython Windows Forms dialog and sweep logic invoked by the Advanced Sweep Tool command. |
| `source/SweepTools/src/scripts/alibre_setup.py` | Bootstrap script that resolves `CurrentPart` / `CurrentAssembly` from the active session. |
| `source/SweepTools/src/logo.ico` | Menu and command icon referenced by the manifest and command. |
| `source/PipeTool.py` | Standalone Alibre Script version of the sweep using the Alibre Script `OptionsDialog`. |
| `source/alibre.disclaimer.txt` | Alibre disclaimer text. |

## Key Folders

| Folder | Purpose |
| --- | --- |
| `source/` | Add-on project source, scripts, and the standalone `PipeTool.py` reference script. |
| `source/SweepTools/src/` | Project source: `AlibreAddOn.vb`, solution and project files, manifest, and icon. |
| `source/SweepTools/src/scripts/` | IronPython scripts the add-on runs (`Template.py`, `alibre_setup.py`). |
| `source/SweepTools/src/bin/Release/net481/` | Prebuilt add-on output, including `SweepTools.dll`, the manifest, the `scripts/` folder, and IronPython DLLs. |
| `documentation/` | Changelog and documentation files (currently placeholders). |
| `submodules/alibre-script-adk/` | Alibre Script ADK Git submodule, including the SelectionListBox contribution. |
| `.github/` | Repository docs, issue and pull request templates, and this README. |

## Notes

- IronPython 2.7.10 runs the scripts, so keep them Python 2.7 compatible.
- `SweepTools.vbproj` references Alibre assemblies by absolute path under `C:\Program Files\Alibre Design 29.0.0.29060\...`. Adjust the `HintPath` entries for a different install location or version.
- `Template.py` sets the chosen units, builds a `SweepProfilePlane` and a `SweepProfile` sketch, then calls `AddSweepBoss` across the entire path. It removes those intermediate features if the sweep fails and can reset the dialog for another run.
- The `documentation/CHANGELOG.md` and `documentation/DOCUMENTATION.md` files are placeholders.
- `submodules/alibre-script-adk` is a Git submodule. Initialize submodules if you need its contents.

## License

See [LICENSE](../LICENSE). The project is released under the MIT License.
