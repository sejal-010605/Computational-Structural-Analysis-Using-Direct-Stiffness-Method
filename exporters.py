import os

import pandas as pd


def export_excel(results, path):
    
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        results["displacements"].to_excel(writer, sheet_name="Displacements", index=False)
        results["reactions"].to_excel(writer, sheet_name="Reactions", index=False)
        results["member_forces"].to_excel(writer, sheet_name="MemberForces", index=False)
        if not results["settlements"].empty:
            results["settlements"].to_excel(writer, sheet_name="Settlements", index=False)

        proj = pd.DataFrame(
            list(results["project_summary"].items()), columns=["Metric", "Value"]
        )
        ana = pd.DataFrame(
            list(results["analysis_summary"].items()), columns=["Metric", "Value"]
        )
        proj.to_excel(writer, sheet_name="ProjectSummary", index=False)
        ana.to_excel(writer, sheet_name="AnalysisSummary", index=False)
    return path


def export_csv(results, directory):
    
    os.makedirs(directory, exist_ok=True)
    results["displacements"].to_csv(os.path.join(directory, "displacements.csv"), index=False)
    results["reactions"].to_csv(os.path.join(directory, "reactions.csv"), index=False)
    results["member_forces"].to_csv(os.path.join(directory, "member_forces.csv"), index=False)
    if not results["settlements"].empty:
        results["settlements"].to_csv(os.path.join(directory, "settlements.csv"), index=False)
    return directory


def export_report(results, path):
    
    lines = []
    bar = "=" * 64

    lines.append(bar)
    lines.append("STRUCTURAL ANALYSIS REPORT".center(64))
    lines.append("2D Frame Analysis - Direct Stiffness Method".center(64))
    lines.append(bar)
    lines.append("")

    lines.append("PROJECT SUMMARY")
    lines.append("-" * 64)
    for k, v in results["project_summary"].items():
        lines.append(f"  {k:<24}: {v}")
    lines.append("")

    lines.append("ANALYSIS SUMMARY")
    lines.append("-" * 64)
    for k, v in results["analysis_summary"].items():
        lines.append(f"  {k:<24}: {v}")
    lines.append("")

    lines.append("NODAL DISPLACEMENTS")
    lines.append("-" * 64)
    lines.append(results["displacements"].to_string(index=False))
    lines.append("")

    if not results["settlements"].empty:
        lines.append("SUPPORT SETTLEMENTS")
        lines.append("-" * 64)
        lines.append(results["settlements"].to_string(index=False))
        lines.append("")

    lines.append("SUPPORT REACTIONS  (kN, kN-m)")
    lines.append("-" * 64)
    lines.append(results["reactions"].to_string(index=False))
    lines.append("")

    lines.append("MEMBER END FORCES  (kN, kN-m)")
    lines.append("-" * 64)
    lines.append(results["member_forces"].to_string(index=False))
    lines.append("")
    lines.append(bar)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path
