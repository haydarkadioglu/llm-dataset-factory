from __future__ import annotations

import os
import threading
import datetime as dt
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Tuple

from src.config import AppConfig
from src.services.groq_client import GroqService
from src.services.gemini_client import GeminiService
from src.loaders.document_loader import load_documents
from src.dataset.builder import DatasetBuilder, chunk_text
from src.settings import load_settings, save_settings


class DatasetApp(tk.Tk):
	def __init__(self) -> None:
		super().__init__()
		self.title("Dataset Factory - LLM Providers")
		self.geometry("860x740")

		self.selected_files: List[str] = []
		self.settings = load_settings()

		self.provider_presets: dict[str, List[tuple[str, bool]]] = {
			"Groq": [
				("openai/gpt-oss-20b", False),
				("openai/gpt-oss-120b", True),
				("qwen/qwen3-32b", False),
			],
			"Gemini": [
				("gemini-2.5-flash", False),
				("gemini-2.0-flash", False),
				("gemini-2.0-flash-lite", True),
			],
		}

		self.file_list = tk.Listbox(self, selectmode=tk.EXTENDED, width=100, height=10)
		self.file_list.pack(padx=10, pady=10)

		btn_frame = tk.Frame(self)
		btn_frame.pack(padx=10, pady=5)

		self.btn_add = tk.Button(btn_frame, text="Add files", command=self.add_files)
		self.btn_add.grid(row=0, column=0, padx=5)

		self.btn_clear = tk.Button(btn_frame, text="Clear", command=self.clear_files)
		self.btn_clear.grid(row=0, column=1, padx=5)

		self.provider_label = tk.Label(btn_frame, text="Provider:")
		self.provider_label.grid(row=0, column=2, padx=5)
		self.provider_var = tk.StringVar(value="Groq")
		self.provider_menu = tk.OptionMenu(btn_frame, self.provider_var, "Groq", "Gemini")
		self.provider_menu.grid(row=0, column=3, padx=5)

		self.model_preset_label = tk.Label(btn_frame, text="Preset:")
		self.model_preset_label.grid(row=0, column=4, padx=5)
		self.model_preset_var = tk.StringVar(value="Custom")
		self.model_preset_menu = tk.OptionMenu(btn_frame, self.model_preset_var, "Custom")
		self.model_preset_menu.grid(row=0, column=5, padx=5)

		self.model_label = tk.Label(btn_frame, text="Model:")
		self.model_label.grid(row=0, column=6, padx=5)
		self.model_entry = tk.Entry(btn_frame, width=28)
		self.model_entry.grid(row=0, column=7, padx=5)

		self.pairs_label = tk.Label(btn_frame, text="#pairs/chunk:")
		self.pairs_label.grid(row=0, column=8, padx=5)
		self.pairs_entry = tk.Entry(btn_frame, width=5)
		self.pairs_entry.insert(0, "3")
		self.pairs_entry.grid(row=0, column=9, padx=5)

		prompt_frame = tk.LabelFrame(self, text="Custom Prompt (optional)")
		prompt_frame.pack(fill=tk.BOTH, padx=10, pady=10, expand=True)
		self.prompt_text = tk.Text(prompt_frame, height=8, wrap=tk.WORD)
		self.prompt_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
		if isinstance(self.settings.get("prompt"), str):
			self.prompt_text.insert("1.0", self.settings.get("prompt", ""))

		out_frame = tk.Frame(self)
		out_frame.pack(fill=tk.X, padx=10, pady=5)
		self.out_label = tk.Label(out_frame, text="Output folder:")
		self.out_label.grid(row=0, column=0, padx=5, sticky="w")
		self.output_dir_var = tk.StringVar(value=self.settings.get("output_dir", "output"))
		self.out_entry = tk.Entry(out_frame, textvariable=self.output_dir_var, width=60)
		self.out_entry.grid(row=0, column=1, padx=5, sticky="we")
		self.btn_browse_out = tk.Button(out_frame, text="Browse", command=self.choose_output_dir)
		self.btn_browse_out.grid(row=0, column=2, padx=5)
		out_frame.grid_columnconfigure(1, weight=1)

		progress_frame = tk.Frame(self)
		progress_frame.pack(fill=tk.X, padx=10, pady=10)
		self.progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
		self.progress.pack(fill=tk.X, padx=5)
		self.progress_var = tk.StringVar(value="Idle")
		self.progress_label = tk.Label(progress_frame, textvariable=self.progress_var, anchor="w")
		self.progress_label.pack(fill=tk.X, padx=5, pady=4)

		self.btn_run = tk.Button(self, text="Generate JSONL", command=self.run_generation)
		self.btn_run.pack(pady=10)

		self.status_var = tk.StringVar(value="Ready")
		self.status = tk.Label(self, textvariable=self.status_var, anchor="w")
		self.status.pack(fill=tk.X, padx=10, pady=5)

		self.provider_var.trace_add("write", lambda *_: self._on_provider_change())
		self.model_preset_var.trace_add("write", lambda *_: self._on_preset_change())
		self._on_provider_change()

	def _recommended_for(self, provider: str) -> str:
		presets = self.provider_presets.get(provider, [])
		for name, rec in presets:
			if rec:
				return name
		return presets[0][0] if presets else ""

	def _rebuild_preset_menu(self, provider: str) -> None:
		menu = self.model_preset_menu["menu"]
		menu.delete(0, "end")
		menu.add_command(label="Custom", command=lambda v="Custom": self.model_preset_var.set(v))
		for name, rec in self.provider_presets.get(provider, []):
			label = f"{name}{' (recommended)' if rec else ''}"
			menu.add_command(label=label, command=lambda v=name: self.model_preset_var.set(v))
		self.model_preset_var.set("Custom")

	def _on_provider_change(self) -> None:
		provider = self.provider_var.get()
		self._rebuild_preset_menu(provider)
		rec = self._recommended_for(provider)
		self.model_entry.delete(0, tk.END)
		self.model_entry.insert(0, rec)

	def _on_preset_change(self) -> None:
		preset = self.model_preset_var.get()
		if preset != "Custom":
			self.model_entry.delete(0, tk.END)
			self.model_entry.insert(0, preset)

	def choose_output_dir(self) -> None:
		selected = filedialog.askdirectory(title="Select output folder")
		if selected:
			self.output_dir_var.set(selected)
			self.persist_settings()

	def persist_settings(self) -> None:
		prompt_value = self.prompt_text.get("1.0", tk.END).strip()
		output_dir = self.output_dir_var.get().strip() or "output"
		save_settings({
			"prompt": prompt_value,
			"output_dir": output_dir,
		})

	def add_files(self) -> None:
		paths = filedialog.askopenfilenames(
			title="Select documents",
			filetypes=[
				("All Supported", "*.txt *.md *.pdf *.py *.cpp *.ipynb *.bat *.sh"),
				("Text/Markdown", "*.txt *.md"),
				("Code Files", "*.py *.cpp *.bat *.sh *.ipynb"),
				("Notebooks", "*.ipynb"),
				("Scripts", "*.bat *.sh"),
				("PDF", "*.pdf"),
				("Text", "*.txt"),
				("Markdown", "*.md"),
				("Python", "*.py"),
				("C++", "*.cpp"),
			]
		)
		if not paths:
			return
		for p in paths:
			if p not in self.selected_files:
				self.selected_files.append(p)
				self.file_list.insert(tk.END, p)

	def clear_files(self) -> None:
		self.selected_files.clear()
		self.file_list.delete(0, tk.END)

	def _set_controls_state(self, state: str) -> None:
		for w in [self.btn_add, self.btn_clear, self.provider_menu, self.model_preset_menu, self.model_entry, self.pairs_entry, self.btn_browse_out, self.btn_run]:
			try:
				w.configure(state=state)
			except Exception:
				pass

	def run_generation(self) -> None:
		if not self.selected_files:
			messagebox.showwarning("No files", "Please add at least one file.")
			return

		self.persist_settings()
		self._set_controls_state("disabled")
		self.status_var.set("Preparing...")
		self.progress_var.set("Chunking documents...")
		self.update_idletasks()

		# Prepare data and chunk counts on UI thread first
		docs = load_documents(self.selected_files)
		all_chunks: List[Tuple[str, str]] = []  # list of (path, chunk)
		for path, text in docs:
			for ch in chunk_text(text):
				all_chunks.append((path, ch))

		total = max(len(all_chunks), 1)
		self.progress.configure(maximum=total, value=0)

		provider = self.provider_var.get()
		model = self.model_entry.get().strip() or None
		num_pairs = int(self.pairs_entry.get().strip() or "3")
		user_prompt = self.prompt_text.get("1.0", tk.END).strip() or None

		config = AppConfig.from_env()
		if provider == "Gemini":
			llm = GeminiService(config)
			if not model:
				model = self._recommended_for("Gemini")
		else:
			llm = GroqService(config)
			if not model:
				model = self._recommended_for("Groq")

		builder = DatasetBuilder(llm)

		results: List[dict] = []

		def worker() -> None:
			try:
				processed = 0
				for _path, chunk in all_chunks:
					pairs = llm.synthesize_qa_pairs(
						(f"{user_prompt}\n\nTEXT:\n{chunk}" if user_prompt else chunk),
						model=model,
						num_pairs=num_pairs,
					)
					for pair in pairs:
						results.append({"input": pair["input"], "output": pair["output"]})
					processed += 1
					self.after(0, self._update_progress, processed, total)

				self.after(0, self._on_generation_done, results)
			except Exception as exc:
				self.after(0, self._on_generation_error, str(exc))

		threading.Thread(target=worker, daemon=True).start()

	def _update_progress(self, processed: int, total: int) -> None:
		self.progress.configure(value=processed)
		self.progress_var.set(f"Processed {processed}/{total} chunks")

	def _on_generation_done(self, records: List[dict]) -> None:
		self.status_var.set("Completed")
		# Ensure output directory
		output_dir = self.output_dir_var.get().strip() or "output"
		os.makedirs(output_dir, exist_ok=True)
		# Default file name as timestamp
		ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
		default_path = os.path.join(output_dir, f"dataset_{ts}.jsonl")
		out_path = filedialog.asksaveasfilename(
			title="Save dataset",
			initialdir=output_dir,
			initialfile=os.path.basename(default_path),
			defaultextension=".jsonl",
			filetypes=[("JSON Lines", "*.jsonl"), ("All Files", "*.*")],
		)
		if out_path:
			DatasetBuilder.save_jsonl(records, out_path)
			self.status_var.set(f"Saved: {out_path}")
			messagebox.showinfo("Done", f"Saved {len(records)} records to {out_path}")
		self._set_controls_state("normal")
		self.progress_var.set("Idle")
		self.progress.configure(value=0)

	def _on_generation_error(self, message: str) -> None:
		self._set_controls_state("normal")
		self.progress_var.set("Idle")
		self.progress.configure(value=0)
		self.status_var.set("Error")
		messagebox.showerror("Error", message)


def run_app() -> None:
	app = DatasetApp()
	app.mainloop()
