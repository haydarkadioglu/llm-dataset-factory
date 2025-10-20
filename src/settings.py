from __future__ import annotations

import json
import os
from typing import Dict, Any


_DEFAULTS = {
	"prompt": "",
	"output_dir": "output",
}


def _settings_path() -> str:
	# Store in project root next to main.py
	return os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.json")


def load_settings() -> Dict[str, Any]:
	path = _settings_path()
	if not os.path.exists(path):
		return dict(_DEFAULTS)
	try:
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		if not isinstance(data, dict):
			return dict(_DEFAULTS)
		merged = dict(_DEFAULTS)
		merged.update({k: v for k, v in data.items() if k in _DEFAULTS})
		return merged
	except Exception:
		return dict(_DEFAULTS)


def save_settings(data: Dict[str, Any]) -> None:
	merged = dict(_DEFAULTS)
	for k in list(data.keys()):
		if k not in _DEFAULTS:
			data.pop(k)
	merged.update(data)
	path = _settings_path()
	try:
		with open(path, "w", encoding="utf-8") as f:
			json.dump(merged, f, ensure_ascii=False, indent=2)
	except Exception:
		# Best effort; ignore persistence errors
		pass
