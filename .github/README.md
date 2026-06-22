# Sweep Tools for Alibre Design

Sweep Tools is an Alibre Design add-on that adds an **Advanced Sweep Tool** for generating solid or hollow swept parts (pipes, tubes, and profiled members) from an existing sketch path. Instead of manually building a profile plane and cross-section, you select a path sketch, pick a profile shape and size, and the add-on creates the profile and the sweep feature for you.

## Features
- Create a swept solid from any 2D or 3D path sketch in the active part.
- Choose a **circular** or **rectangular** cross-section profile, sized in your preferred units.
- Optionally generate a **hollow** profile (tube/pipe) by specifying a wall thickness.
- Work in **millimeters, inches, or centimeters**, with live unit labels in the dialog.
- Pick the path sketch interactively from the Alibre workspace via a live selection list.
- Input validation and automatic cleanup of intermediate plane/sketch features if a sweep fails, with an option to keep the dialog open for creating multiple sweeps.

## Requirements
- Alibre Design with the AlibreScript add-on installed (developed against Alibre Design 29.0.0.29060).
- .NET Framework 4.8.1 (the add-on targets `net481`, x64).
- IronPython 2.7 (bundled with the add-on; the sweep logic runs as embedded Python scripts).

## Installation
The add-on is a managed DLL described by the `SweepTools.adc` manifest, which Alibre uses to register and load it at startup.

1. Build `source/SweepTools/src/SweepTools.sln` in Release configuration, or use the prebuilt output under `source/SweepTools/src/bin/Release/net481/`.
2. Copy the build output, `SweepTools.dll`, `SweepTools.adc`, `logo.ico`, the `scripts/` folder, and the bundled IronPython DLLs, into a folder under your Alibre Design add-ons location.
3. Start Alibre Design. The "Sweep Tools" add-on loads automatically and appears in the add-ons menu.

## Usage
1. Open a part and create the sketch you want to use as the sweep path (a 2D or 3D sketch containing a curve).
2. From the **Sweep Tools** menu, choose **Advanced Sweep Tool** to open the dialog.
3. Click the path sketch list, then select your path sketch in the workspace. Check **Use 3D Path** if it is a 3D sketch.
4. Choose the units, profile type (Circle or Rectangle), and profile size. To make a tube, enable **Create hollow profile** and set the wall thickness.
5. Click **Advanced Sweep Tool** to create the sweep. Enable **Stay open after creating** to keep the dialog open for additional sweeps.

## License
See [LICENSE](../LICENSE).
