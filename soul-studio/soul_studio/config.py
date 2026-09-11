"""Konfiguration: config.yaml + Umgebungsvariablen (.env)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent          # soul-studio/
REPO_ROOT = ROOT.parent                                # Repo-Wurzel


def _load_dotenv(path: Path) -> None:
    """Minimaler .env-Loader (keine Abhängigkeit von python-dotenv)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


class BrandColors(BaseModel):
    burgundy: str = "#4A081E"
    cream: str = "#FAF7F0"
    deep_salmon: str = "#983D15"
    salmon: str = "#FCA27A"
    pale_salmon: str = "#FEC7AF"
    tint: str = "#FFF2EB"


class BrandConfig(BaseModel):
    name: str = "Desk Revolution"
    claim: str = "Die Zukunft der Assistenzrolle."
    handle: str = "@deskrevolution"
    website: str = "deskrevolution.de"
    colors: BrandColors = BrandColors()
    font_headline: str = "Playfair Display"
    font_body: str = "League Spartan"


class CharacterConfig(BaseModel):
    name: str = "steffi"
    soul_id: str = ""
    variant: Literal["soul-2", "soul-cinematic"] = "soul-2"
    photos_dir: str = "soul-studio/character/photos"
    look: str = (
        "a woman in her thirties with a warm, calm and confident expression, "
        "modern smart-casual business outfit in muted cream and burgundy tones, "
        "natural make-up, realistic skin, photographic"
    )
    setting: str = (
        "bright modern office or home office, soft daylight, clean desk, laptop, "
        "warm cream and burgundy accents, shallow depth of field"
    )


class VoiceConfig(BaseModel):
    provider: Literal["elevenlabs", "higgsfield"] = "elevenlabs"
    elevenlabs_voice_id: str = ""
    elevenlabs_model: str = "eleven_v3"
    language: str = "de"
    stability: float = 0.5
    similarity_boost: float = 0.8
    style: float = 0.2
    speed: float = 1.0
    higgsfield_voice_id: str = ""
    higgsfield_voice_type: Literal["preset", "element"] = "preset"
    higgsfield_variant: str = "elevenlabs"


class ModelsConfig(BaseModel):
    image: str = "text2image_soul_v2"
    image_quality: str = "2k"
    talking_video: str = "seedance_2_5"
    talking_video_mode: str = "std"
    talking_video_resolution: str = "1080p"
    broll_video: str = "kling3_0"
    broll_video_mode: str = "pro"
    broll_seconds: int = 5
    still_image: str = "text2image_soul_v2"


class VideoConfig(BaseModel):
    aspect_ratio: str = "9:16"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    target_seconds: int = 45
    min_blocks: int = 4
    max_blocks: int = 7
    max_words_per_block: int = 22
    mode: Literal["talking_head", "mixed", "broll_only"] = "mixed"
    captions: Literal["word", "line", "none"] = "word"
    caption_words_per_chunk: int = 3
    end_card_seconds: float = 2.5
    end_card_text: str = "Desk Revolution"
    end_card_sub: str = "Die Zukunft der Assistenzrolle."
    wait_timeout: str = "20m"


class LLMConfig(BaseModel):
    model: str = "claude-opus-5"
    effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"
    max_tokens: int = 16000


class NotionSourceConfig(BaseModel):
    database_id: str = ""
    status_property: str = "Status"
    ready_value: str = "Video erstellen"
    done_value: str = "Video erstellt"
    title_property: str = "Name"
    text_property: str = "Text"


class SourcesConfig(BaseModel):
    posts_dir: str = "content/posts"
    extensions: list[str] = Field(default_factory=lambda: [".md", ".txt", ".html"])
    notion: NotionSourceConfig = NotionSourceConfig()


class MetricoolConfig(BaseModel):
    user_id: str = ""
    blog_id: str = ""
    networks: list[str] = Field(default_factory=lambda: ["tiktok", "instagram"])
    timezone: str = "Europe/Berlin"
    schedule_offset_hours: int = 24
    draft: bool = True


class PublishConfig(BaseModel):
    enabled: bool = False
    public_base_url: str = "https://stweyland.github.io/Desk-R"
    metricool: MetricoolConfig = MetricoolConfig()


class Settings(BaseModel):
    brand: BrandConfig = BrandConfig()
    character: CharacterConfig = CharacterConfig()
    voice: VoiceConfig = VoiceConfig()
    models: ModelsConfig = ModelsConfig()
    video: VideoConfig = VideoConfig()
    llm: LLMConfig = LLMConfig()
    sources: SourcesConfig = SourcesConfig()
    publish: PublishConfig = PublishConfig()
    output_dir: str = "soul-studio/output"
    state_file: str = "soul-studio/state/processed.json"
    fonts_dir: str = "soul-studio/assets/fonts"
    prompts_dir: str = "soul-studio/prompts"

    # --- Pfade relativ zur Repo-Wurzel auflösen -------------------------
    def path(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else REPO_ROOT / p

    @property
    def output_path(self) -> Path:
        return self.path(self.output_dir)

    @property
    def state_path(self) -> Path:
        return self.path(self.state_file)

    @property
    def fonts_path(self) -> Path:
        return self.path(self.fonts_dir)

    @property
    def prompts_path(self) -> Path:
        return self.path(self.prompts_dir)

    # --- Secrets aus der Umgebung ---------------------------------------
    @property
    def elevenlabs_api_key(self) -> str:
        return os.environ.get("ELEVENLABS_API_KEY", "")

    @property
    def notion_token(self) -> str:
        return os.environ.get("NOTION_TOKEN", "")

    @property
    def metricool_token(self) -> str:
        return os.environ.get("METRICOOL_TOKEN", "")

    @property
    def higgsfield_bin(self) -> str:
        return os.environ.get("HIGGSFIELD_BIN", "higgsfield")


def load_settings(config_path: Path | None = None) -> Settings:
    _load_dotenv(ROOT / ".env")
    _load_dotenv(REPO_ROOT / ".env")
    path = config_path or Path(os.environ.get("SOUL_STUDIO_CONFIG", ROOT / "config.yaml"))
    data: dict = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = Settings.model_validate(data)
    # Umgebungsvariablen dürfen einzelne Werte überschreiben
    if os.environ.get("SOUL_ID"):
        settings.character.soul_id = os.environ["SOUL_ID"]
    if os.environ.get("ELEVENLABS_VOICE_ID"):
        settings.voice.elevenlabs_voice_id = os.environ["ELEVENLABS_VOICE_ID"]
    if os.environ.get("SOUL_STUDIO_LLM_MODEL"):
        settings.llm.model = os.environ["SOUL_STUDIO_LLM_MODEL"]
    return settings
