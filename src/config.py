import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class AppConfig:
	groq_api_key: str | None
	gemini_api_key: str | None
	default_model: str = "llama-3.1-70b-versatile"
	default_gemini_model: str = "gemini-1.5-pro"

	@staticmethod
	def from_env() -> "AppConfig":
		groq_key = os.getenv("GROQ_API_KEY", "").strip() or None
		gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or None
		if not groq_key and not gemini_key:
			raise ValueError("Provide GROQ_API_KEY or GEMINI_API_KEY in environment.")
		return AppConfig(groq_api_key=groq_key, gemini_api_key=gemini_key)
