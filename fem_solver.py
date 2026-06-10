import math

import numpy as np
import pandas as pd

def get_dof(node, dof):
    return (node - 1) * 3 + dof


def length(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def angle(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)


def local_stiffness(E, A, I, L):
    return np.array([
        [A * E / L, 0, 0, -A * E / L, 0, 0],
        [0, 12 * E * I / L ** 3, 6 * E * I / L ** 2, 0, -12 * E * I / L ** 3, 6 * E * I / L ** 2],
        [0, 6 * E * I / L ** 2, 4 * E * I / L, 0, -6 * E * I / L ** 2, 2 * E * I / L],
        [-A * E / L, 0, 0, A * E / L, 0, 0],
        [0, -12 * E * I / L ** 3, -6 * E * I / L ** 2, 0, 12 * E * I / L ** 3, -6 * E * I / L ** 2],
        [0, 6 * E * I / L ** 2, 2 * E * I / L, 0, -6 * E * I / L ** 2, 4 * E * I / L],
    ])


def transformation(theta):
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [c, s, 0, 0, 0, 0],
        [-s, c, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, c, s, 0],
        [0, 0, 0, -s, c, 0],
        [0, 0, 0, 0, 0, 1],
    ])


def fef_local(w1, w2, L):
    w1 = -w1
    w2 = -w2
    f = np.zeros((6, 1))
    f[1][0] = (7 * w1 + 3 * w2) * L / 20
    f[2][0] = (3 * w1 + 2 * w2) * L ** 2 / 60
    f[4][0] = (3 * w1 + 7 * w2) * L / 20
    f[5][0] = -(2 * w1 + 3 * w2) * L ** 2 / 60
    return f


def fef_uvl_3point(w1, w2, w3, L):
    w_avg = (w1 + w2 + w3) / 3
    return fef_local(w_avg, w_avg, L)



class SolverError(Exception):
    """Raised for validation and numerical problems the UI should surface."""


class StructuralSolver:
    REQUIRED_SHEETS = ("Nodes", "Members", "Loads")

    NODE_COLUMNS = [
        "Node", "X", "Y", "H", "V", "M",
        "ux_free", "uy_free", "rz_free",
        "ux_val", "uy_val", "rz_val",
    ]
    MEMBER_COLUMNS = ["Member", "Node_i", "Node_j", "E", "A", "I"]
    LOAD_COLUMNS = ["Member", "w1", "w2", "w3"]

    def __init__(self):
        self.nodes = None
        self.members = None
        self.loads = None

        self.results = {}
        self._loaded = False

    
    #  Input
    
    def load_excel(self, path):
        """Read the three required sheets and validate their structure."""
        try:
            xls = pd.ExcelFile(path)
        except Exception as exc:  # noqa: BLE001
            raise SolverError(f"Unable to open Excel file:\n{exc}") from exc

        missing = [s for s in self.REQUIRED_SHEETS if s not in xls.sheet_names]
        if missing:
            raise SolverError(
                "The workbook is missing required sheet(s): "
                + ", ".join(missing)
                + ".\nExpected sheets: Nodes, Members, Loads."
            )

        self.nodes = pd.read_excel(path, sheet_name="Nodes")
        self.members = pd.read_excel(path, sheet_name="Members")
        self.loads = pd.read_excel(path, sheet_name="Loads")

        self._validate_columns()
        self._validate_values()
        self._loaded = True

    def _validate_columns(self):
        def check(df, cols, sheet):
            missing = [c for c in cols if c not in df.columns]
            if missing:
                raise SolverError(
                    f"Sheet '{sheet}' is missing column(s): {', '.join(missing)}."
                )

        check(self.nodes, self.NODE_COLUMNS, "Nodes")
        check(self.members, self.MEMBER_COLUMNS, "Members")
        check(self.loads, ["Member", "w1", "w2"], "Loads")

        # Ensure optional load column exists so member_fef logic is safe.
        if "w3" not in self.loads.columns:
            self.loads["w3"] = 0.0

    def _validate_values(self):
        if self.nodes.empty:
            raise SolverError("The 'Nodes' sheet contains no nodes.")
        if self.members.empty:
            raise SolverError("The 'Members' sheet contains no members.")

        if self.nodes[["X", "Y"]].isnull().any().any():
            raise SolverError("One or more nodes have missing X/Y coordinates.")

        if self.members[["E", "A", "I"]].isnull().any().any():
            raise SolverError("One or more members have missing E, A or I values.")

        valid_nodes = set(self.nodes["Node"].astype(int))
        for _, m in self.members.iterrows():
            for end in ("Node_i", "Node_j"):
                if int(m[end]) not in valid_nodes:
                    raise SolverError(
                        f"Member {int(m['Member'])} references undefined "
                        f"node {int(m[end])}."
                    )

    
    #  Fixed end forces for a member
    
    def _member_fef(self, member_id, L):
        f = np.zeros((6, 1))
        member_loads = self.loads[self.loads["Member"] == member_id]
        for _, row in member_loads.iterrows():
            if row["w3"] != 0:
                f += fef_uvl_3point(row["w1"], row["w2"], row["w3"], L)
            else:
                f += fef_local(row["w1"], row["w2"], L)
        return f

    
    #  Analysis 
    def analyze(self):
        if not self._loaded:
            raise SolverError("No model has been imported yet.")

        nodes = self.nodes
        members = self.members

        n_nodes = len(nodes)
        total_dofs = n_nodes * 3

        K_global = np.zeros((total_dofs, total_dofs))
        F_global = np.zeros((total_dofs, 1))

        #Global assembly
        for _, m in members.iterrows():
            i = int(m["Node_i"])
            j = int(m["Node_j"])

            xi, yi = nodes.loc[nodes["Node"] == i, ["X", "Y"]].values[0]
            xj, yj = nodes.loc[nodes["Node"] == j, ["X", "Y"]].values[0]

            L = length(xi, yi, xj, yj)
            if L == 0:
                raise SolverError(
                    f"Member {int(m['Member'])} has zero length "
                    f"(nodes {i} and {j} are coincident)."
                )
            theta = angle(xi, yi, xj, yj)

            k_local = local_stiffness(m["E"], m["A"], m["I"], L)
            T = transformation(theta)

            k_global = T.T @ k_local @ T
            fef = self._member_fef(m["Member"], L)
            fef_global = T.T @ fef

            dof_map = [
                get_dof(i, 0), get_dof(i, 1), get_dof(i, 2),
                get_dof(j, 0), get_dof(j, 1), get_dof(j, 2),
            ]

            for a in range(6):
                for b in range(6):
                    K_global[dof_map[a], dof_map[b]] += k_global[a, b]
            for a in range(6):
                F_global[dof_map[a]] -= fef_global[a]

        #Nodal loads
        for _, n in nodes.iterrows():
            node = int(n["Node"])
            F_global[get_dof(node, 0)] += n["H"]
            F_global[get_dof(node, 1)] += n["V"]
            F_global[get_dof(node, 2)] += n["M"]

        #Boundary conditions
        free_dofs = []
        fixed_dofs = []
        U_known = []

        for _, n in nodes.iterrows():
            node = int(n["Node"])
            for idx, key in enumerate(["ux_free", "uy_free", "rz_free"]):
                dof = get_dof(node, idx)
                if n[key] == 1:
                    free_dofs.append(dof)
                else:
                    fixed_dofs.append(dof)
                    U_known.append(n[["ux_val", "uy_val", "rz_val"][idx]])

        if not free_dofs:
            raise SolverError(
                "The structure has no free degrees of freedom to solve for."
            )

        U_known = np.array(U_known, dtype=float).reshape(-1, 1)

        K_uu = K_global[np.ix_(free_dofs, free_dofs)]
        K_uk = K_global[np.ix_(free_dofs, fixed_dofs)]
        F_u = F_global[free_dofs]

        #Solve
        try:
            U_u = np.linalg.solve(K_uu, F_u - K_uk @ U_known)
        except np.linalg.LinAlgError as exc:
            raise SolverError(
                "Singular stiffness matrix encountered.\n"
                "The structure is unstable or inadequately restrained "
                "(check supports and connectivity)."
            ) from exc

        #Displacement vector
        U = np.zeros((total_dofs, 1))
        for idx, d in enumerate(free_dofs):
            U[d] = U_u[idx]
        for idx, d in enumerate(fixed_dofs):
            U[d] = U_known[idx]

        #Reactions
        R = K_global @ U - F_global

        #Member end forces
        member_forces = []
        for _, m in members.iterrows():
            i = int(m["Node_i"])
            j = int(m["Node_j"])

            xi, yi = nodes.loc[nodes["Node"] == i, ["X", "Y"]].values[0]
            xj, yj = nodes.loc[nodes["Node"] == j, ["X", "Y"]].values[0]

            L = length(xi, yi, xj, yj)
            theta = angle(xi, yi, xj, yj)

            k_local = local_stiffness(m["E"], m["A"], m["I"], L)
            T = transformation(theta)

            dof_map = [
                get_dof(i, 0), get_dof(i, 1), get_dof(i, 2),
                get_dof(j, 0), get_dof(j, 1), get_dof(j, 2),
            ]

            Ue = np.array([U[dof_map[k]][0] for k in range(6)]).reshape(6, 1)
            U_local = T @ Ue

            fef = self._member_fef(m["Member"], L)
            F_local = k_local @ U_local + fef

            member_forces.append({
                "Member": int(m["Member"]),
                "Axial_i (kN)": F_local[0][0],
                "Shear_i (kN)": F_local[1][0],
                "Moment_i (kN-m)": F_local[2][0],
                "Axial_j (kN)": F_local[3][0],
                "Shear_j (kN)": F_local[4][0],
                "Moment_j (kN-m)": F_local[5][0],
            })

        #Results for the UI
        self.results = self._package(
            nodes, U, U_u, U_known, R, member_forces,
            free_dofs, fixed_dofs, total_dofs,
        )
        return self.results

    
    def _package(self, nodes, U, U_u, U_known, R, member_forces,
                 free_dofs, fixed_dofs, total_dofs):
        dof_label = {0: "Ux", 1: "Uy", 2: "Rz"}

        # Per-DOF displacement table
        disp_rows = []
        for _, n in nodes.iterrows():
            node = int(n["Node"])
            for idx in range(3):
                dof = get_dof(node, idx)
                disp_rows.append({
                    "Node": node,
                    "DOF": dof_label[idx],
                    "Type": "Free" if dof in free_dofs else "Fixed",
                    "Displacement (mm)": U[dof][0] * 1000,
                })
        displacements = pd.DataFrame(disp_rows)

        # Support reactions
        reaction_rows = []
        for _, n in nodes.iterrows():
            if n["ux_free"] == 0 or n["uy_free"] == 0 or n["rz_free"] == 0:
                node = int(n["Node"])
                reaction_rows.append({
                    "Node": node,
                    "Rx (kN)": R[get_dof(node, 0)][0],
                    "Ry (kN)": R[get_dof(node, 1)][0],
                    "Mz (kN-m)": R[get_dof(node, 2)][0],
                })
        reactions = pd.DataFrame(reaction_rows)

        # Support settlements 
        settle_rows = []
        for _, n in nodes.iterrows():
            node = int(n["Node"])
            for idx, key in enumerate(["ux_free", "uy_free", "rz_free"]):
                val_key = ["ux_val", "uy_val", "rz_val"][idx]
                if n[key] == 0 and float(n[val_key]) != 0.0:
                    settle_rows.append({
                        "Node": node,
                        "DOF": dof_label[idx],
                        "Prescribed Value": float(n[val_key]),
                    })
        settlements = pd.DataFrame(settle_rows)

        forces = pd.DataFrame(member_forces)

        n_supports = int(
            ((nodes["ux_free"] == 0)
             | (nodes["uy_free"] == 0)
             | (nodes["rz_free"] == 0)).sum()
        )

        return {
            "displacements": displacements,
            "unknown_dofs": U_u.flatten(),
            "known_dofs": U_known.flatten(),
            "settlements": settlements,
            "reactions": reactions,
            "member_forces": forces,
            "project_summary": {
                "Nodes": len(self.nodes),
                "Members": len(self.members),
                "Loads": len(self.loads),
                "Supports": n_supports,
            },
            "analysis_summary": {
                "Solver Type": "Direct Stiffness Method",
                "Analysis Status": "Completed",
                "Total DOF": total_dofs,
                "Free DOF": len(free_dofs),
                "Fixed DOF": len(fixed_dofs),
            },
        }
