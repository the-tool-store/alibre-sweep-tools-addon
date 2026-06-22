# SOURCE:https://www.alibre.com/forum/index.php?threads/ai-scripting-new-tools-into-alibre.26141/#post-179976
# Alibre Script: Advanced Sweep (Single Sketch Method)
# Creates a solid or hollow sweep from a single profile sketch.
import sys

# Establish handles for the main Alibre objects
MyPart = CurrentPart()
Win = Windows()

# --- 1. Define and Display the Menu ---
Units.Current = UnitTypes.Millimeters

# Define the layout of the static dialog window
Options = []
Options.append(['Path Sketch', WindowsInputTypes.Sketch, None])
Options.append(['Profile Type', WindowsInputTypes.StringList, ['Circle', 'Square']])
Options.append(['Size (mm)', WindowsInputTypes.Real, 10.0])
Options.append(['Hollow', WindowsInputTypes.Boolean, False])
Options.append(['Thickness (mm)', WindowsInputTypes.Real, 1.0])

# Show the options dialog
Values = Win.OptionsDialog('Create Advanced Sweep', Options, 220)

# Exit the script if the user cancels the dialog
if Values is None or Values[0] is None:
  print "Operation cancelled or no path sketch selected."
  sys.exit()

# --- 2. Process Inputs ---
PathSketch = Values[0]
ProfileTypeIndex = Values[1]
ProfileSize = Values[2]
IsHollow = Values[3]
Thickness = Values[4]

# --- Define the Profile Plane (Works for Lines and Splines) ---
FirstFigure = PathSketch.Figures[0]
Is3DSketch = '3D' in PathSketch.GetType().Name

if hasattr(FirstFigure, 'GetPointAt'): # Spline logic
  # Sample the spline at the start and at a small parameter delta to get the
  # start tangent. A closed/looped spline or a near-zero start tangent over a
  # tiny interval can yield a degenerate direction vector, so try progressively
  # larger deltas until the direction is non-zero.
  def SampleDirection(Delta):
    if Is3DSketch:
      SP = FirstFigure.GetPointAt(0.0)
      NP = FirstFigure.GetPointAt(Delta)
    else:
      SP2 = FirstFigure.GetPointAt(0.0)
      NP2 = FirstFigure.GetPointAt(Delta)
      SP = PathSketch.PointtoGlobal(SP2[0], SP2[1])
      NP = PathSketch.PointtoGlobal(NP2[0], NP2[1])
    return SP, NP

  StartPoint3D = None
  DirectionVector = [0.0, 0.0, 0.0]
  for Delta in [0.001, 0.01, 0.1, 0.25]:
    StartPoint3D, NextPoint3D = SampleDirection(Delta)
    DirectionVector = [NextPoint3D[i] - StartPoint3D[i] for i in range(3)]
    Magnitude = (DirectionVector[0] ** 2 + DirectionVector[1] ** 2 + DirectionVector[2] ** 2) ** 0.5
    if Magnitude > 1e-9:
      break
else: # Line logic
  if Is3DSketch:
    StartPoint3D = FirstFigure.StartPoint
    NextPoint3D = FirstFigure.EndPoint
  else:
    StartPoint2D = FirstFigure.StartPoint
    NextPoint2D = FirstFigure.EndPoint
    StartPoint3D = PathSketch.PointtoGlobal(StartPoint2D[0], StartPoint2D[1])
    NextPoint3D = PathSketch.PointtoGlobal(NextPoint2D[0], NextPoint2D[1])
  DirectionVector = [NextPoint3D[i] - StartPoint3D[i] for i in range(3)]

# Validate the direction vector is non-zero before creating the plane;
# a zero vector makes AddPlane fail or build a malformed plane.
Magnitude = (DirectionVector[0] ** 2 + DirectionVector[1] ** 2 + DirectionVector[2] ** 2) ** 0.5
if Magnitude < 1e-9:
  print "Could not determine a valid sweep direction from the path's start tangent. Aborting."
  sys.exit()

ProfilePlane = MyPart.AddPlane('SweepProfilePlane', DirectionVector, StartPoint3D)

# --- 3. Create a Single Profile Sketch ---
ProfileSketch = MyPart.AddSketch('SweepProfile', ProfilePlane)

# Draw the outer profile shape based on the index from the dropdown
if ProfileTypeIndex == 0: # Circle
  OuterSize = ProfileSize
  ProfileSketch.AddCircle(0, 0, OuterSize, False)
elif ProfileTypeIndex == 1: # Square
  OuterHalf = ProfileSize / 2.0
  ProfileSketch.AddRectangle(-OuterHalf, -OuterHalf, OuterHalf, OuterHalf, False)

# If hollow is checked, draw the inner profile ON THE SAME SKETCH
if IsHollow and Thickness > 0 and Thickness < ProfileSize:
  if ProfileTypeIndex == 0: # Circle
    InnerSize = ProfileSize - Thickness
    ProfileSketch.AddCircle(0, 0, InnerSize, False)
  elif ProfileTypeIndex == 1: # Square
    InnerSize = ProfileSize - (Thickness * 2)
    InnerHalf = InnerSize / 2.0
    ProfileSketch.AddRectangle(-InnerHalf, -InnerHalf, InnerHalf, InnerHalf, False)

# --- 4. Perform the Sweep ---
# Regenerate the part to ensure the sketch (with one or two loops) is finalized
MyPart.Regenerate()

# Create the sweep feature using the single profile sketch
MyPart.AddSweepBoss('Sweep', ProfileSketch, PathSketch, False, MyPart.EndCondition.EntirePath, None, 0, 0, False)

print "Script finished."