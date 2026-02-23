from __future__ import annotations

import tkinter as tk
from datetime import datetime


class SubmitTestDialog:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Submit AutoClicker Test")
        self.root.geometry("460x220")
        self.root.resizable(False, False)

        frame = tk.Frame(self.root, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        title = tk.Label(
            frame,
            text="Auto-Clicker Desktop Test",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(anchor="w", pady=(0, 8))

        question = tk.Label(
            frame,
            text="Do you approve this automation test?",
            font=("Segoe UI", 11),
        )
        question.pack(anchor="w", pady=(0, 8))

        self.status_var = tk.StringVar(value="Waiting for the Submit button to be auto-clicked...")
        self.status = tk.Label(
            frame,
            textvariable=self.status_var,
            wraplength=420,
            justify="left",
            fg="#334155",
            font=("Segoe UI", 10),
        )
        self.status.pack(anchor="w", pady=(0, 12))

        button_row = tk.Frame(frame)
        button_row.pack(anchor="w")

        self.submit_button = tk.Button(
            button_row,
            text="Submit",
            width=14,
            state="disabled",
            command=self.on_submit,
        )
        self.submit_button.pack(side="left")

        close_button = tk.Button(
            button_row,
            text="Close",
            width=10,
            command=self.root.destroy,
        )
        close_button.pack(side="left", padx=(10, 0))

        # Delay enable to simulate a button appearing after content is ready.
        self.root.after(2500, self.enable_submit)

    def enable_submit(self) -> None:
        self.submit_button.config(state="normal")
        self.status_var.set("Submit button enabled. If bot is live, it should click automatically.")

    def on_submit(self) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"Submit clicked at {timestamp}. Test succeeded.")
        self.status.config(fg="#166534")
        print(f"submit_clicked_at={timestamp}")

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    app = SubmitTestDialog()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

