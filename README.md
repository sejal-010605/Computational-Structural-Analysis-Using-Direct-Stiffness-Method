# Computational Structural Analysis Using Direct Stiffness Method

## Overview
This project presents a generalized Python implementation of the Direct Stiffness Method for elastic analysis of 2D plane frames. The program accepts geometry, material properties, support conditions, and loading data through Excel input files and computes structural response automatically.

## Objectives
- Develop a generic structural analysis tool using Python.
- Implement the Direct Stiffness Method for 2D frame analysis.
- Handle vertical, horizontal, and inclined frame members.
- Compute nodal displacements, support reactions, and member end forces.
- Provide a user-friendly graphical interface for analysis and result visualization.

## Key Features
- Excel-based input system
- Direct Stiffness Method implementation
- Support for all types of supports
- Point loads, UDL, UVL, and trapezoidal loads
- Displacement calculation
- Support reaction calculation
- Member end force calculation
- Export results to Excel/CSV
- Modern graphical user interface

## Input Data
The program reads the following information from Excel files:

### Nodes
- Node Number
- X Coordinate
- Y Coordinate
- Boundary Conditions
- Applied Nodal Loads

### Members
- Member Number
- Start Node
- End Node
- Young's Modulus (E)
- Cross-sectional Area (A)
- Moment of Inertia (I)

### Loads
- Point Loads
- Uniformly Distributed Loads (UDL)
- Uniformly Varying Loads (UVL)
- Trapezoidal Loads

## Outputs
The software provides:

- Nodal Displacements
- Support Reactions
- Member End Forces

## Sample Structure
The repository includes a sample frame model demonstrating:
- Fixed and pinned supports
- Inclined members
- Distributed loading
- Horizontal loading

## Technologies Used
- Python
- NumPy
- Pandas
- OpenPyXL
- CustomTkinter

## Project Structure
```text
app.py                -> Main GUI application
fem_solver.py         -> Direct Stiffness Method solver
ui_components.py      -> UI components
exporters.py          -> Export utilities
sample_model.py       -> Sample model generator
```

## How to Run
1. Clone the repository
2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the application

```bash
python app.py
```

## Results
The application computes:

- Displacements at known and unknown DOFs
- Support Reactions
- Member End Forces

## Author
Sejal 
