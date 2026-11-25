"""Desktop interface for configuring and running game batches."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from queue import Empty, Queue
from tkinter import messagebox, ttk

from ..experiments import BatchRunner
from ..game.model.modules import MODULE_DEFINITIONS
from ..game.model.state import Difficulty

_DIFFICULTIES = {
    "Easiest": Difficulty.EASIEST,
    "Easy": Difficulty.EASY,
    "Medium": Difficulty.MEDIUM,
    "Hard": Difficulty.HARD,
    "Hardest": Difficulty.HARDEST,
}


class GameSetupWindow:
    """Collect game settings and run the requested batch."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Nature Solo Bot")
        self.root.minsize(360, 300)
        # The worker thread returns results here so only the Tk thread updates widgets.
        self._results: Queue[tuple[int, Path] | Exception] = Queue()
        self._module_vars: dict[str, tk.BooleanVar] = {}
        self._promo_vars: dict[str, tk.BooleanVar] = {}
        self._promo_buttons: dict[str, ttk.Checkbutton] = {}
        self._build_interface()
        self.root.after(100, self._check_results)

    def _build_interface(self) -> None:
        """Create settings controls, promo toggles, status text, and the run button."""
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(1, weight=1)

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

        ttk.Separator(container).grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)
        ttk.Label(container, text="Nature promo cards").grid(
            row=3, column=0, sticky=tk.W, padx=(0, 12), pady=4
        )
        self.nature_promo = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            container,
            text="Include",
            variable=self.nature_promo,
        ).grid(row=3, column=1, sticky=tk.W, pady=4)

        ttk.Label(container, text="Modules").grid(
            row=4, column=0, sticky=tk.W, padx=(0, 12), pady=(8, 2)
        )
        module_frame = ttk.Frame(container)
        module_frame.grid(row=4, column=1, sticky=tk.EW, pady=(8, 2))
        for row, module in enumerate(MODULE_DEFINITIONS):
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

        ttk.Separator(container).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(container, textvariable=self.status, wraplength=330).grid(
            row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 8)
        )
        self.run_button = ttk.Button(container, text="Run games", command=self._start_batch)
        self.run_button.grid(row=7, column=0, columnspan=2, sticky=tk.EW)

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

        modules = [module for module, selected in self._module_vars.items() if selected.get()]
        promo_modules = [
            module
            for module in modules
            if self._promo_vars[module].get()
        ]
        include_promo = self.nature_promo.get() or bool(promo_modules)
        output_directory = (
            Path("output")
            / "Nature"
            / difficulty_name.lower()
            / ("promo" if include_promo else "core")
        )
        if modules:
            output_directory /= "+".join(modules)

        self.run_button.configure(state=tk.DISABLED)
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
                output_directory,
            ),
            daemon=True,
        ).start()

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
            ).run(output_directory)
        except Exception as error:
            self._results.put(error)
            return
        self._results.put((len(log_paths), output_directory))

    def _check_results(self) -> None:
        """Poll worker results on Tk's event loop and update the window safely."""
        try:
            payload = self._results.get_nowait()
        except Empty:
            self.root.after(100, self._check_results)
            return

        self.run_button.configure(state=tk.NORMAL)
        if isinstance(payload, Exception):
            self.status.set("The batch did not complete.")
            messagebox.showerror("Batch failed", str(payload))
        else:
            count, output_directory = payload
            self.status.set(f"Saved {count} game logs to {output_directory}")
        self.root.after(100, self._check_results)


def main() -> None:
    """Open the game setup window."""
    root = tk.Tk()
    GameSetupWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
