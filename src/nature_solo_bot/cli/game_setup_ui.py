"""Desktop interface for configuring and running game batches."""

from __future__ import annotations

import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from tkinter import filedialog, messagebox, ttk

from ..experiments import BatchRunner
from ..game.model.modules import MODULE_DEFINITIONS
from ..game.model.state import Difficulty
from .analyze_traits import run_analysis

_DEFAULT_OUTPUT_FOLDER = Path("output") / "Nature"
_LAST_OUTPUT_FOLDER_FILE = Path.home() / ".nature_solo_bot" / "last_output_folder.txt"
_ANALYSIS_OPTIONS = (
    ("Trait assignments", "trait_assignments"),
    ("Food by trait", "food_by_trait"),
    ("Trait combinations", "trait_combinations"),
    ("Solo species", "solo_species"),
)

_DIFFICULTIES = {
    "Easiest": Difficulty.EASIEST,
    "Easy": Difficulty.EASY,
    "Medium": Difficulty.MEDIUM,
    "Hard": Difficulty.HARD,
    "Hardest": Difficulty.HARDEST,
}


@dataclass(frozen=True)
class _OperationFailure:
    operation: str
    error: Exception


def _load_last_output_folder(settings_file: Path) -> str:
    """Load the last chosen folder, using the default when no setting exists."""
    try:
        saved_folder = settings_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return str(_DEFAULT_OUTPUT_FOLDER)
    return saved_folder or str(_DEFAULT_OUTPUT_FOLDER)


def _save_last_output_folder(folder: str, settings_file: Path) -> None:
    """Persist the chosen folder in the user's home directory."""
    selected_folder = Path(folder).expanduser().resolve()
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(str(selected_folder), encoding="utf-8")


def _analysis_directories(selected_folder: str) -> tuple[Path, Path]:
    """Resolve the selected run or simulations folder to logs and report folders."""
    selected_directory = Path(selected_folder).expanduser().resolve()
    if selected_directory.name.casefold() == "simulations":
        return selected_directory, selected_directory.parent / "analysis"

    simulations_directory = selected_directory / "simulations"
    if simulations_directory.is_dir():
        return simulations_directory, selected_directory / "analysis"
    return selected_directory, selected_directory.parent / "analysis"


class GameSetupWindow:
    """Collect game settings and run the requested batch."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Nature Solo Bot")
        self.root.minsize(390, 350)
        # The worker thread returns results here so only the Tk thread updates widgets.
        self._results: Queue[tuple[str, int, int | Path] | _OperationFailure] = Queue()
        self._module_vars: dict[str, tk.BooleanVar] = {}
        self._promo_vars: dict[str, tk.BooleanVar] = {}
        self._promo_buttons: dict[str, ttk.Checkbutton] = {}
        self._analysis_vars: dict[str, tk.BooleanVar] = {}
        self._settings_file = _LAST_OUTPUT_FOLDER_FILE
        self._build_interface()
        self.root.after(100, self._check_results)

    def _build_interface(self) -> None:
        """Create the simulations and analysis tabs."""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)
        simulations_tab = ttk.Frame(notebook, padding=16)
        analysis_tab = ttk.Frame(notebook, padding=16)
        notebook.add(simulations_tab, text="Run simulations")
        notebook.add(analysis_tab, text="Analysis")
        self._build_simulations_tab(simulations_tab)
        self._build_analysis_tab(analysis_tab)

    def _build_simulations_tab(self, container: ttk.Frame) -> None:
        """Create simulation settings, promo toggles, status text, and the run button."""
        container.columnconfigure(1, weight=1)
        container.rowconfigure(4, weight=1)
        container.columnconfigure(2, weight=0)

        ttk.Label(container, text="Number of games").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 12), pady=4
        )
        self.game_count = tk.StringVar(value="1000")
        ttk.Entry(container, textvariable=self.game_count, width=12).grid(
            row=0, column=1, sticky=tk.W, pady=4
        )

        ttk.Label(container, text="Difficulty").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 12), pady=4
        )
        self.difficulty = tk.StringVar(value="Medium")
        ttk.Combobox(
            container,
            textvariable=self.difficulty,
            values=tuple(_DIFFICULTIES),
            state="readonly",
            width=12,
        ).grid(row=1, column=1, sticky=tk.W, pady=4)

        ttk.Label(container, text="Output folder").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 12), pady=4
        )
        try:
            initial_output_folder = _load_last_output_folder(self._settings_file)
        except OSError as error:
            initial_output_folder = str(_DEFAULT_OUTPUT_FOLDER)
            messagebox.showwarning(
                "Could not load output folder",
                f"Using the default folder instead.\n\n{error}",
            )
        self.output_directory = tk.StringVar(value=initial_output_folder)
        ttk.Entry(container, textvariable=self.output_directory).grid(
            row=2, column=1, sticky=tk.EW, pady=4
        )
        ttk.Button(
            container,
            text="Browse...",
            command=self._choose_output_folder,
        ).grid(row=2, column=2, sticky=tk.E, padx=(8, 0), pady=4)

        ttk.Separator(container).grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        ttk.Label(container, text="Modules").grid(
            row=4, column=0, sticky=tk.NW, padx=(0, 12), pady=(8, 2)
        )
        module_area = ttk.Frame(container)
        module_area.grid(row=4, column=1, columnspan=2, sticky=tk.NSEW, pady=(8, 2))
        module_area.columnconfigure(0, weight=1)
        module_area.rowconfigure(1, weight=1)
        ttk.Button(
            module_area,
            text="Select all promos",
            command=self._select_all_promos,
        ).grid(row=0, column=0, columnspan=2, sticky=tk.E, pady=(0, 4))

        module_canvas = tk.Canvas(module_area, height=130, highlightthickness=0)
        module_canvas.grid(row=1, column=0, sticky=tk.NSEW)
        module_scrollbar = ttk.Scrollbar(
            module_area,
            orient=tk.VERTICAL,
            command=module_canvas.yview,
        )
        module_scrollbar.grid(row=1, column=1, sticky=tk.NS)
        module_canvas.configure(yscrollcommand=module_scrollbar.set)
        module_frame = ttk.Frame(module_canvas)
        module_window = module_canvas.create_window(
            (0, 0),
            window=module_frame,
            anchor=tk.NW,
        )
        module_frame.bind(
            "<Configure>",
            lambda _event: module_canvas.configure(
                scrollregion=module_canvas.bbox("all")
            ),
        )
        module_canvas.bind(
            "<Configure>",
            lambda event: module_canvas.itemconfigure(module_window, width=event.width),
        )
        self.nature_promo = tk.BooleanVar(value=False)
        ttk.Label(module_frame, text="Core").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 12), pady=2
        )
        ttk.Checkbutton(
            module_frame,
            text="Promo",
            variable=self.nature_promo,
        ).grid(row=0, column=1, sticky=tk.W, pady=2)

        for row, module in enumerate(MODULE_DEFINITIONS, start=1):
            module_var = tk.BooleanVar(value=False)
            promo_var = tk.BooleanVar(value=False)
            self._module_vars[module] = module_var
            self._promo_vars[module] = promo_var

            # Keep each module's Promo control disabled until its module is selected.
            ttk.Checkbutton(
                module_frame,
                text=module.replace("_", " ").title(),
                variable=module_var,
                command=lambda name=module: self._update_promo_state(name),
            ).grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=2)
            promo_check = ttk.Checkbutton(
                module_frame,
                text="Promo",
                variable=promo_var,
            )
            promo_check.grid(row=row, column=1, sticky=tk.W, pady=2)
            self._promo_buttons[module] = promo_check
            self._update_promo_state(module)

        ttk.Separator(container).grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=10)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(container, textvariable=self.status, wraplength=330).grid(
            row=6, column=0, columnspan=3, sticky=tk.W, pady=(0, 8)
        )
        self.progress = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            container,
            variable=self.progress,
            maximum=1,
            mode="determinate",
        )
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=tk.EW, pady=(0, 8))
        self.run_button = ttk.Button(container, text="Run games", command=self._start_batch)
        self.run_button.grid(row=8, column=0, columnspan=3, sticky=tk.EW)

    def _build_analysis_tab(self, container: ttk.Frame) -> None:
        """Create folder selection and report controls."""
        container.columnconfigure(1, weight=1)
        ttk.Label(container, text="Simulation folder").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 12), pady=4
        )
        self.analysis_directory = tk.StringVar(value="")
        ttk.Entry(container, textvariable=self.analysis_directory).grid(
            row=0, column=1, sticky=tk.EW, pady=4
        )
        ttk.Button(
            container,
            text="Browse...",
            command=self._choose_analysis_folder,
        ).grid(row=0, column=2, sticky=tk.E, padx=(8, 0), pady=4)

        ttk.Label(container, text="Reports").grid(
            row=1, column=0, sticky=tk.NW, padx=(0, 12), pady=(12, 4)
        )
        options_frame = ttk.Frame(container)
        options_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(12, 4))
        for row, (label, key) in enumerate(_ANALYSIS_OPTIONS):
            selected = tk.BooleanVar(value=True)
            self._analysis_vars[key] = selected
            ttk.Checkbutton(options_frame, text=label, variable=selected).grid(
                row=row, column=0, sticky=tk.W, pady=2
            )

        self.analysis_status = tk.StringVar(value="Ready")
        ttk.Label(container, textvariable=self.analysis_status, wraplength=380).grid(
            row=2, column=0, columnspan=3, sticky=tk.W, pady=(12, 8)
        )
        self.run_analysis_button = ttk.Button(
            container,
            text="Run analysis",
            command=self._start_analysis,
        )
        self.run_analysis_button.grid(row=3, column=0, columnspan=3, sticky=tk.EW)

    def _choose_output_folder(self) -> None:
        """Let the user choose the exact folder where game logs will be saved."""
        current_directory = Path(self.output_directory.get()).expanduser()
        selected_directory = filedialog.askdirectory(
            title="Choose output folder",
            initialdir=str(current_directory) if current_directory.is_dir() else None,
            mustexist=True,
        )
        if selected_directory:
            self.output_directory.set(selected_directory)
            self._remember_output_folder(selected_directory)

    def _choose_analysis_folder(self) -> None:
        """Let the user choose a run folder or its simulations subfolder."""
        selected_folder = self.analysis_directory.get().strip()
        current_directory = (
            Path(selected_folder).expanduser()
            if selected_folder
            else _DEFAULT_OUTPUT_FOLDER
        )
        selected_directory = filedialog.askdirectory(
            title="Choose simulation run folder",
            initialdir=str(current_directory) if current_directory.is_dir() else None,
            mustexist=True,
        )
        if selected_directory:
            self.analysis_directory.set(selected_directory)

    def _remember_output_folder(self, folder: str) -> None:
        """Save a selected folder and notify the user if the preference cannot persist."""
        try:
            _save_last_output_folder(folder, self._settings_file)
        except OSError as error:
            messagebox.showwarning(
                "Could not remember output folder",
                f"The folder will be used for this run, but could not be saved for next time.\n\n{error}",
            )

    def _select_all_promos(self) -> None:
        """Enable Core Promo cards and promos for currently selected modules."""
        self.nature_promo.set(True)
        for module in self._module_vars:
            self._update_promo_state(module)
            if self._module_vars[module].get():
                self._promo_vars[module].set(True)

    def _update_promo_state(self, module: str) -> None:
        """Enable a module's Promo option only while that module is selected."""
        self._promo_buttons[module].configure(
            state=tk.NORMAL if self._module_vars[module].get() else tk.DISABLED
        )
        # Clear hidden selections so deselecting a module cannot retain its Promo cards.
        if not self._module_vars[module].get():
            self._promo_vars[module].set(False)

    def _start_batch(self) -> None:
        """Validate the selected settings and start the batch off the UI thread."""
        try:
            game_count = int(self.game_count.get())
        except ValueError:
            messagebox.showerror("Invalid number of games", "Enter a whole number greater than zero.")
            return
        if game_count <= 0:
            messagebox.showerror("Invalid number of games", "Enter a whole number greater than zero.")
            return

        difficulty_name = self.difficulty.get()
        if difficulty_name not in _DIFFICULTIES:
            messagebox.showerror("Invalid difficulty", "Select one of the listed difficulties.")
            return
        output_folder = self.output_directory.get().strip()
        if not output_folder:
            messagebox.showerror("Invalid output folder", "Choose a folder for the game logs.")
            return
        self._remember_output_folder(output_folder)

        modules = [module for module, selected in self._module_vars.items() if selected.get()]
        promo_modules = [
            module
            for module in modules
            if self._promo_vars[module].get()
        ]
        output_root = Path(output_folder).expanduser()
        run_directory = (
            output_root
            / datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
            / "simulations"
        )
        try:
            run_directory.mkdir(parents=True, exist_ok=False)
        except OSError as error:
            messagebox.showerror("Could not create run folder", str(error))
            return

        self.run_button.configure(state=tk.DISABLED)
        self.run_analysis_button.configure(state=tk.DISABLED)
        self.progress.set(0)
        self.progress_bar.configure(maximum=game_count)
        self.status.set("Running games...")
        # Game simulations can take time; keep Tk responsive while they run.
        threading.Thread(
            target=self._run_batch,
            args=(
                game_count,
                _DIFFICULTIES[difficulty_name],
                modules,
                promo_modules,
                self.nature_promo.get(),
                run_directory,
            ),
            daemon=True,
        ).start()

    def _start_analysis(self) -> None:
        """Validate selected reports and run them in a worker thread."""
        selected_folder = self.analysis_directory.get().strip()
        if not selected_folder:
            messagebox.showerror("Invalid simulation folder", "Choose a folder containing game logs.")
            return
        log_directory, analysis_directory = _analysis_directories(selected_folder)
        if not log_directory.is_dir():
            messagebox.showerror(
                "Invalid simulation folder",
                f"The folder does not exist:\n{log_directory}",
            )
            return

        analyses = [
            key for key, selected in self._analysis_vars.items() if selected.get()
        ]
        if not analyses:
            messagebox.showerror("No analysis selected", "Select at least one report to run.")
            return

        try:
            analysis_directory.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror("Could not create analysis folder", str(error))
            return

        self.run_button.configure(state=tk.DISABLED)
        self.run_analysis_button.configure(state=tk.DISABLED)
        self.analysis_status.set("Running analysis...")
        threading.Thread(
            target=self._run_analysis,
            args=(log_directory, analysis_directory, analyses),
            daemon=True,
        ).start()

    def _run_analysis(
        self,
        log_directory: Path,
        analysis_directory: Path,
        analyses: list[str],
    ) -> None:
        """Run reports off the UI thread and queue completion or failure."""
        try:
            output_paths = run_analysis(log_directory, analysis_directory, analyses)
        except Exception as error:
            self._results.put(_OperationFailure("analysis", error))
            return
        self._results.put(("analysis_complete", len(output_paths), analysis_directory))

    def _run_batch(
        self,
        game_count: int,
        difficulty: Difficulty,
        modules: list[str],
        promo_modules: list[str],
        nature_promo: bool,
        output_directory: Path,
    ) -> None:
        """Run simulations in a worker and send completion or failure to the UI queue."""
        try:
            log_paths = BatchRunner(
                game_count=game_count,
                difficulty=difficulty,
                modules=modules,
                promo_modules=promo_modules,
                nature_promo=nature_promo,
            ).run(
                output_directory,
                progress_callback=lambda completed, total: self._results.put(
                    ("progress", completed, total)
                ),
                numbered_logs=True,
            )
        except Exception as error:
            self._results.put(_OperationFailure("batch", error))
            return
        self._results.put(("complete", len(log_paths), output_directory))

    def _check_results(self) -> None:
        """Poll worker results on Tk's event loop and update the window safely."""
        while True:
            try:
                payload = self._results.get_nowait()
            except Empty:
                break

            if isinstance(payload, _OperationFailure):
                self.run_button.configure(state=tk.NORMAL)
                self.run_analysis_button.configure(state=tk.NORMAL)
                if payload.operation == "analysis":
                    self.analysis_status.set("The analysis did not complete.")
                    messagebox.showerror("Analysis failed", str(payload.error))
                else:
                    self.status.set("The batch did not complete.")
                    messagebox.showerror("Batch failed", str(payload.error))
            else:
                result, completed, detail = payload
                if result == "progress":
                    self.progress.set(completed)
                    self.status.set(f"Running games: {completed} of {detail}")
                elif result == "analysis_complete":
                    self.run_button.configure(state=tk.NORMAL)
                    self.run_analysis_button.configure(state=tk.NORMAL)
                    self.analysis_status.set(
                        f"Saved {completed} analysis reports to {detail}"
                    )
                else:
                    self.run_button.configure(state=tk.NORMAL)
                    self.run_analysis_button.configure(state=tk.NORMAL)
                    self.progress.set(completed)
                    self.status.set(f"Saved {completed} game logs to {detail}")
        self.root.after(100, self._check_results)


def main() -> None:
    """Open the game setup window."""
    root = tk.Tk()
    GameSetupWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
