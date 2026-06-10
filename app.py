import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from fem_solver import StructuralSolver, SolverError
from ui_components import (
    Theme, font, Card, StatCard, InfoRow, DataTable, Badge,
)
import exporters
import sample_model
ctk.set_appearance_mode("light")


class StructuralAnalysisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Structural Analysis ")
        self.geometry("1280x820")
        self.minsize(1080, 720)
        self.configure(fg_color=Theme.BG)

        self.solver = StructuralSolver()
        self.results = None
        self.model_path = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_topbar()
        self._build_body()

        self._set_status("Ready", Theme.TEXT_MUTED)

    
    #  Top bar
    
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=Theme.SURFACE, corner_radius=0,
                           height=72, border_width=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_propagate(False)

        # Brand
        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w", padx=28, pady=14)

        logo = ctk.CTkLabel(
            brand, text="◧", font=font(26, "bold"), text_color=Theme.ACCENT,
        )
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ctk.CTkLabel(
            brand, text="Structural Analysis", font=font(18, "bold"),
            text_color=Theme.TEXT, anchor="w",
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            brand, text="Direct Stiffness Method  ·  2D Frame",
            font=font(11), text_color=Theme.TEXT_MUTED, anchor="w",
        ).grid(row=1, column=1, sticky="w")

        # Actions
        actions = ctk.CTkFrame(bar, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e", padx=28)

        self.import_btn = ctk.CTkButton(
            actions, text="Import Excel Model", width=170, height=40,
            corner_radius=10, font=font(13, "bold"),
            fg_color=Theme.SURFACE, text_color=Theme.ACCENT,
            border_width=1, border_color=Theme.ACCENT,
            hover_color=Theme.BADGE_BG, command=self.on_import,
        )
        self.import_btn.grid(row=0, column=0, padx=(0, 10))

        self.run_btn = ctk.CTkButton(
            actions, text="Run Analysis", width=150, height=40,
            corner_radius=10, font=font(13, "bold"),
            fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
            text_color="#FFFFFF", command=self.on_run,
        )
        self.run_btn.grid(row=0, column=1)

    
    #  Sidebar and content
    
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=24)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_sidebar(body)
        self._build_content(body)

    def _build_sidebar(self, parent):
        side = ctk.CTkFrame(parent, fg_color="transparent", width=320)
        side.grid(row=0, column=0, sticky="nsw", padx=(0, 24))
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        # Intro card
        hero = Card(side)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        hero.grid_columnconfigure(0, weight=1)

        Badge(hero, "Direct Stiffness Method").grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 12))
        ctk.CTkLabel(
            hero, text="Structural Analysis\nUsing Direct\nStiffness Method",
            font=font(22, "bold"), text_color=Theme.TEXT, justify="left", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=20)
        ctk.CTkLabel(
            hero,
            text=("Generic elastic structural analysis software using the Direct Stiffness Method for vertical and inclined plane frames, with Excel-based input for geometry, member data, supports, and loading conditions."),
            font=font(12), text_color=Theme.TEXT_MUTED, justify="left",
            anchor="w", wraplength=260,
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(10, 20))

        # Workflow steps
        steps_card = Card(side)
        steps_card.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        steps_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            steps_card, text="WORKFLOW", font=font(11, "bold"),
            text_color=Theme.TEXT_MUTED, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 10))

        self.step_widgets = []
        steps = [
            "Import Excel File",
            "Validate Input Data",
            "Run FEM Analysis",
            "Display Results",
            "Export Results",
        ]
        for i, label in enumerate(steps):
            row = ctk.CTkFrame(steps_card, fg_color="transparent")
            row.grid(row=i + 1, column=0, sticky="ew", padx=20, pady=5)
            row.grid_columnconfigure(1, weight=1)
            dot = ctk.CTkLabel(
                row, text=str(i + 1), width=26, height=26, corner_radius=13,
                font=font(11, "bold"), fg_color=Theme.BORDER,
                text_color=Theme.TEXT_MUTED,
            )
            dot.grid(row=0, column=0, padx=(0, 12))
            txt = ctk.CTkLabel(
                row, text=label, font=font(13), text_color=Theme.TEXT_MUTED,
                anchor="w",
            )
            txt.grid(row=0, column=1, sticky="w")
            self.step_widgets.append((dot, txt))

        # Sample model helper
        self.sample_btn = ctk.CTkButton(
            steps_card, text="Generate Sample Model", height=36,
            corner_radius=10, font=font(12, "bold"),
            fg_color="transparent", text_color=Theme.ACCENT,
            border_width=1, border_color=Theme.BORDER,
            hover_color=Theme.BADGE_BG, command=self.on_generate_sample,
        )
        self.sample_btn.grid(row=len(steps) + 1, column=0, sticky="ew",
                             padx=20, pady=(14, 20))

        # File status
        self.file_card = Card(side)
        self.file_card.grid(row=2, column=0, sticky="ew")
        self.file_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.file_card, text="ACTIVE MODEL", font=font(11, "bold"),
            text_color=Theme.TEXT_MUTED, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 4))
        self.file_label = ctk.CTkLabel(
            self.file_card, text="No file imported", font=font(13),
            text_color=Theme.TEXT, anchor="w", wraplength=260, justify="left",
        )
        self.file_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 18))

    def _build_content(self, parent):
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        #Summary cards row
        summary = ctk.CTkFrame(content, fg_color="transparent")
        summary.grid(row=0, column=0, sticky="ew")
        for c in range(4):
            summary.grid_columnconfigure(c, weight=1, uniform="stat")

        self.stat_nodes = StatCard(summary, "Nodes", "—")
        self.stat_members = StatCard(summary, "Members", "—")
        self.stat_loads = StatCard(summary, "Loads", "—")
        self.stat_supports = StatCard(summary, "Supports", "—", accent=True)
        for i, w in enumerate(
            [self.stat_nodes, self.stat_members, self.stat_loads, self.stat_supports]
        ):
            w.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))

        #Analysis summary strip
        ana = Card(content)
        ana.grid(row=1, column=0, sticky="ew", pady=(16, 16))
        for c in range(5):
            ana.grid_columnconfigure(c, weight=1, uniform="ana")

        self.ana_rows = {}
        ana_items = [
            ("Solver Type", "Direct Stiffness"),
            ("Analysis Status", "Idle"),
            ("Total DOF", "—"),
            ("Free DOF", "—"),
            ("Fixed DOF", "—"),
        ]
        for i, (label, value) in enumerate(ana_items):
            box = ctk.CTkFrame(ana, fg_color="transparent")
            box.grid(row=0, column=i, sticky="ew", padx=18, pady=16)
            ctk.CTkLabel(
                box, text=label.upper(), font=font(10, "bold"),
                text_color=Theme.TEXT_MUTED, anchor="w",
            ).grid(row=0, column=0, sticky="w")
            val = ctk.CTkLabel(
                box, text=str(value), font=font(16, "bold"),
                text_color=Theme.TEXT, anchor="w",
            )
            val.grid(row=1, column=0, sticky="w", pady=(2, 0))
            self.ana_rows[label] = val

        #Results tabs
        self.tabs = ctk.CTkTabview(
            content, fg_color=Theme.SURFACE, corner_radius=16,
            border_width=1, border_color=Theme.BORDER,
            segmented_button_fg_color=Theme.BG,
            segmented_button_selected_color=Theme.ACCENT,
            segmented_button_selected_hover_color=Theme.ACCENT_HOVER,
            segmented_button_unselected_color=Theme.BG,
            text_color=Theme.TEXT,
        )
        self.tabs.grid(row=2, column=0, sticky="nsew")

        self.tab_disp = self.tabs.add("Displacements")
        self.tab_react = self.tabs.add("Support Reactions")
        self.tab_forces = self.tabs.add("Member End Forces")

        for tab in (self.tab_disp, self.tab_react, self.tab_forces):
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        self.table_disp = DataTable(self.tab_disp)
        self.table_disp.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        self.table_react = DataTable(self.tab_react)
        self.table_react.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        self.table_forces = DataTable(self.tab_forces)
        self.table_forces.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)

        self._render_empty_state()

        #Bottom bar
        bottom = ctk.CTkFrame(content, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        bottom.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(
            bottom, text="●", font=font(14), text_color=Theme.TEXT_MUTED,
        )
        self.status_dot.grid(row=0, column=0, padx=(2, 8))
        self.status_label = ctk.CTkLabel(
            bottom, text="Ready", font=font(13), text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        self.status_label.grid(row=0, column=1, sticky="w")

        self.progress = ctk.CTkProgressBar(
            bottom, width=200, height=6, corner_radius=3,
            progress_color=Theme.ACCENT, fg_color=Theme.BORDER,
        )
        self.progress.grid(row=0, column=2, padx=16)
        self.progress.set(0)
        self.progress.grid_remove()

        self.export_menu = ctk.CTkOptionMenu(
            bottom, values=["Export Excel", "Export CSV", "Export Report"],
            width=160, height=38, corner_radius=10, font=font(13, "bold"),
            fg_color=Theme.TEXT, button_color=Theme.TEXT,
            button_hover_color="#1E293B", text_color="#FFFFFF",
            command=self.on_export, dropdown_font=font(12),
        )
        self.export_menu.set("Export Results")
        self.export_menu.grid(row=0, column=3)
        self.export_menu.configure(state="disabled")

    
    #  Empty state
    def _render_empty_state(self):
        import pandas as pd
        placeholder = pd.DataFrame()
        self.table_disp.render(placeholder)
        self.table_react.render(placeholder)
        self.table_forces.render(placeholder)

    
    #  Workflow step highlighting
    def _mark_step(self, index, done=True):
        if index < 0 or index >= len(self.step_widgets):
            return
        dot, txt = self.step_widgets[index]
        if done:
            dot.configure(fg_color=Theme.ACCENT, text_color="#FFFFFF")
            txt.configure(text_color=Theme.TEXT)
        else:
            dot.configure(fg_color=Theme.BORDER, text_color=Theme.TEXT_MUTED)
            txt.configure(text_color=Theme.TEXT_MUTED)

    
    #  Status helpers
    def _set_status(self, text, color=Theme.TEXT_MUTED):
        self.status_label.configure(text=text, text_color=color)
        self.status_dot.configure(text_color=color)

    
    #  Actions
    def on_generate_sample(self):
        path = filedialog.asksaveasfilename(
            title="Save sample model",
            defaultextension=".xlsx",
            initialfile="sample_frame.xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
        )
        if not path:
            return
        try:
            sample_model.write_sample(path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Sample Model", f"Could not write sample:\n{exc}")
            return
        self._set_status("Sample model created", Theme.SUCCESS)
        if messagebox.askyesno(
            "Sample Model",
            "Sample model created.\n\nImport it now?",
        ):
            self._load_model(path)

    def on_import(self):
        path = filedialog.askopenfilename(
            title="Import Excel structural model",
            filetypes=[("Excel files", "*.xlsx *.xls")],
        )
        if not path:
            return
        self._load_model(path)

    def _load_model(self, path):
        self._set_status("Importing model…", Theme.ACCENT)
        try:
            self.solver = StructuralSolver()
            self.solver.load_excel(path)
        except SolverError as exc:
            self._set_status("Import failed", Theme.DANGER)
            messagebox.showerror("Validation Error", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            self._set_status("Import failed", Theme.DANGER)
            messagebox.showerror("Import Error", f"Unexpected error:\n{exc}")
            return

        self.model_path = path
        self.results = None
        self.export_menu.configure(state="disabled")
        self.export_menu.set("Export Results")

        self.file_label.configure(text=os.path.basename(path))
        self._mark_step(0, True)
        self._mark_step(1, True)
        for i in range(2, 5):
            self._mark_step(i, False)

        # Refresh project summary cards immediately
        self.stat_nodes.set_value(len(self.solver.nodes))
        self.stat_members.set_value(len(self.solver.members))
        self.stat_loads.set_value(len(self.solver.loads))
        n_supports = int(
            ((self.solver.nodes["ux_free"] == 0)
             | (self.solver.nodes["uy_free"] == 0)
             | (self.solver.nodes["rz_free"] == 0)).sum()
        )
        self.stat_supports.set_value(n_supports)

        self.ana_rows["Analysis Status"].configure(
            text="Ready", text_color=Theme.ACCENT)
        self._render_empty_state()
        self._set_status("Model imported and validated", Theme.SUCCESS)

    def on_run(self):
        if not self.solver._loaded:
            messagebox.showinfo(
                "Run Analysis", "Import an Excel model before running the analysis."
            )
            return

        self.run_btn.configure(state="disabled", text="Analyzing…")
        self.import_btn.configure(state="disabled")
        self.progress.grid()
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self._set_status("Running finite element analysis…", Theme.ACCENT)
        self._mark_step(2, True)

        thread = threading.Thread(target=self._run_worker, daemon=True)
        thread.start()

    def _run_worker(self):
        try:
            results = self.solver.analyze()
            self.after(0, self._on_run_success, results)
        except SolverError as exc:
            self.after(0, self._on_run_error, str(exc))
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._on_run_error, f"Unexpected solver error:\n{exc}")

    def _on_run_success(self, results):
        self.results = results
        self.progress.stop()
        self.progress.grid_remove()
        self.run_btn.configure(state="normal", text="Run Analysis")
        self.import_btn.configure(state="normal")

        # Analysis summary
        a = results["analysis_summary"]
        self.ana_rows["Solver Type"].configure(text="Direct Stiffness")
        self.ana_rows["Analysis Status"].configure(
            text=a["Analysis Status"], text_color=Theme.SUCCESS)
        self.ana_rows["Total DOF"].configure(text=a["Total DOF"])
        self.ana_rows["Free DOF"].configure(text=a["Free DOF"])
        self.ana_rows["Fixed DOF"].configure(text=a["Fixed DOF"])

        # Tables
        self.table_disp.render(
            results["displacements"], float_cols=["Displacement (mm)"], decimals=3)
        self.table_react.render(
            results["reactions"], float_cols=["Rx (kN)", "Ry (kN)", "Mz (kN-m)"], decimals=3)
        self.table_forces.render(
            results["member_forces"],
            float_cols=["Axial_i", "Shear_i", "Moment_i",
                        "Axial_j", "Shear_j", "Moment_j"],
            decimals=4,
        )

        self._mark_step(3, True)
        self.export_menu.configure(state="normal")
        self._set_status("Analysis complete", Theme.SUCCESS)

    def _on_run_error(self, message):
        self.progress.stop()
        self.progress.grid_remove()
        self.run_btn.configure(state="normal", text="Run Analysis")
        self.import_btn.configure(state="normal")
        self._mark_step(2, False)
        self.ana_rows["Analysis Status"].configure(
            text="Failed", text_color=Theme.DANGER)
        self._set_status("Analysis failed", Theme.DANGER)
        messagebox.showerror("Analysis Error", message)

    def on_export(self, choice):
        self.export_menu.set("Export Results")
        if not self.results:
            return
        try:
            if choice == "Export Excel":
                path = filedialog.asksaveasfilename(
                    title="Export to Excel", defaultextension=".xlsx",
                    initialfile="analysis_results.xlsx",
                    filetypes=[("Excel Workbook", "*.xlsx")],
                )
                if path:
                    exporters.export_excel(self.results, path)
                    self._export_done(path)
            elif choice == "Export CSV":
                directory = filedialog.askdirectory(
                    title="Choose folder for CSV files")
                if directory:
                    out = exporters.export_csv(self.results, directory)
                    self._export_done(out)
            elif choice == "Export Report":
                path = filedialog.asksaveasfilename(
                    title="Export report", defaultextension=".txt",
                    initialfile="analysis_report.txt",
                    filetypes=[("Text Report", "*.txt")],
                )
                if path:
                    exporters.export_report(self.results, path)
                    self._export_done(path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Export Error", f"Could not export:\n{exc}")

    def _export_done(self, path):
        self._mark_step(4, True)
        self._set_status(f"Exported: {os.path.basename(path)}", Theme.SUCCESS)
        messagebox.showinfo("Export Complete", f"Results exported to:\n{path}")


def main():
    app = StructuralAnalysisApp()
    app.mainloop()


if __name__ == "__main__":
    main()
