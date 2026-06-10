import pandas as pd

# Steel properties
E = 2.05e11      # Pa
A = 0.04         # m² (0.2m × 0.2m section)
I = 1.333e-4     # m⁴


def build_dataframes():
    """
    Double-frame structure validated against STAAD.Pro

    Supports:
        Node 1 = Fixed
        Node 4 = Fixed
        Node 8 = Pinned
    """

    nodes = pd.DataFrame([
        # Node,X,Y,H,V,M,ux_free,uy_free,rz_free,ux_val,uy_val,rz_val

        [1, 0.0,  0.0,   0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0],
        [2, 0.0, 10.0,   0, 0, 0, 1, 1, 1, 0.0, 0.0, 0.0],
        [3,10.0, 10.0,   0, 0, 0, 1, 1, 1, 0.0, 0.0, 0.0],
        [4,10.0,  0.0,   0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0],
        [5, 5.0, 15.0,   0, 0, 0, 1, 1, 1, 0.0, 0.0, 0.0],
        [6,15.0, 15.0,   0, 0, 0, 1, 1, 1, 0.0, 0.0, 0.0],
        [7,20.0, 10.0,   0, 0, 0, 1, 1, 1, 0.0, 0.0, 0.0],

        # pinned support
        [8,20.0,  0.0,   0, 0, 0, 0, 0, 1, 0.0, 0.0, 0.0],

    ], columns=[
        "Node","X","Y","H","V","M",
        "ux_free","uy_free","rz_free",
        "ux_val","uy_val","rz_val"
    ])

    # Horizontal load at Node 7
    nodes.loc[nodes["Node"] == 7, "H"] = -10000.0

    members = pd.DataFrame([

        [1,1,2,E,A,I],
        [2,2,5,E,A,I],
        [3,5,3,E,A,I],
        [4,3,4,E,A,I],
        [5,3,6,E,A,I],
        [6,6,7,E,A,I],
        [7,7,8,E,A,I],
        [8,2,3,E,A,I],

    ], columns=[
        "Member","Node_i","Node_j","E","A","I"
    ])

    loads = pd.DataFrame([

        # Member,w1,w2,w3

        # Left roof
        [2,-10000.0,-20000.0,0.0],

        # Right side of left roof
        [3,-20000.0,-30000.0,0.0],

        # Left side of right roof
        [5,-30000.0,-20000.0,0.0],

        # Right roof
        [6,0.0,-20000.0,0.0],

    ], columns=[
        "Member","w1","w2","w3"
    ])

    return nodes, members, loads


def write_sample(path="sample_frame.xlsx"):
    nodes, members, loads = build_dataframes()

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        nodes.to_excel(writer, sheet_name="Nodes", index=False)
        members.to_excel(writer, sheet_name="Members", index=False)
        loads.to_excel(writer, sheet_name="Loads", index=False)

    return path


if __name__ == "__main__":
    out = write_sample()
    print(f"Sample model written to: {out}")