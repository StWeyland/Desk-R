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
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


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


class VoiceConfig(BaseModel):
    elevenlabs_voice_id: str = ""
    elevenlabs_model: str = "eleven_v3"
    language: str = "de"
    stability: float = 0.5
    similarity_boost: float = 0.8
    style: float = 0.2
    speed: float = 1.0


class CharacterConfig(BaseModel):
    """Steffis Gesicht: 1–3 gute Fotos (frontal, ruhiger Hintergrund). Pfade oder Umgebungsvariable CHARACTER_PHOTO_URL."""
    photos: list[str] = Field(default_factory=list)
    notion_photo_page: str = ""       # Notion-Seite, auf der die Fotos liegen (die Routine lädt sie von dort)
    look: str = (
        "a woman in her thirties with a warm, calm and confident expression, "
        "modern smart-casual business outfit in muted cream and burgundy tones, natural, photographic"
    )


class FootageConfig(BaseModel):
    provider: Literal["pexels", "fal"] = "pexels"     # B-Roll: pexels = kostenlose Stock-Clips, fal = KI-Clips (bezahlt)
    talking_model: str = "fal-ai/bytedance/omnihuman/v1.5"   # Foto + Stimme → sprechendes Video (ca. 0,16 $/Sek.)
    talking_extra: dict = Field(default_factory=lambda: {"resolution": "1080p"})
    talking_max_seconds: int = 28                     # OmniHuman 1080p: Audio höchstens 30 s je Clip
    fal_model: str = "fal-ai/kling-video/v2.5-turbo/pro/text-to-video"
    image_model: str = "fal-ai/nano-banana-pro"              # Editorial-Illustration ohne Gesicht (ca. 0,15 $/Bild)
    character_image_model: str = "fal-ai/nano-banana-pro/edit"   # Szene MIT Steffis Gesicht (ca. 0,15 $/Bild)
    image_resolution: str = "2K"
    fal_seconds: int = 5
    fal_extra: dict = Field(default_factory=lambda: {"cfg_scale": 0.5})
    style_suffix: str = (
        "cinematic, soft natural daylight, warm cream and burgundy tones, modern office, "
        "shallow depth of field, slow smooth camera movement, no text, no logos, no faces looking at camera"
    )


class VideoConfig(BaseModel):
    aspect_ratio: str = "9:16"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    target_seconds: int = 40
    mode: Literal["talking_head", "mixed", "broll_only"] = "mixed"   # mixed = Hook und Schluss mit Gesicht, dazwischen Szenen
    min_blocks: int = 4
    max_blocks: int = 7
    max_words_per_block: int = 22
    captions: Literal["word", "line", "none"] = "word"
    caption_words_per_chunk: int = 3
    end_card_seconds: float = 2.5
    end_card_text: str = "Desk Revolution"
    end_card_sub: str = "Die Zukunft der Assistenzrolle."
    music: str = ""                                    # optionaler Pfad zu einer Musikdatei (lizenzfrei)
    music_volume: float = 0.12


class CarouselConfig(BaseModel):
    slides: int = 7
    width: int = 1080
    height: int = 1350


class LLMConfig(BaseModel):
    model: str = "claude-opus-5"
    effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"
    max_tokens: int = 16000


class NotionConfig(BaseModel):
    database_url: str = "https://app.notion.com/p/9394d55953204b3d88e53cc2f879d9c4"
    data_source: str = "collection://e2df8581-1dc1-447d-9a80-46e0f2222b6d"
    status_property: str = "Status"
    trigger_status: str = "Produzieren"
    done_status: str = "Zur Freigabe"
    format_property: str = "Format"
    text_property: str = "Entwurfstext"
    asset_property: str = "Asset"
    note_property: str = "Produktions-Notiz"


class MetricoolConfig(BaseModel):
    blog_id: str = "6925448"
    timezone: str = "Europe/Berlin"
    reviewer_email: str = "stefanie@deskr.onmicrosoft.com"
    default_networks: list[str] = Field(default_factory=lambda: ["linkedin"])
    schedule_offset_days: int = 2
    schedule_hour: int = 8


class Settings(BaseModel):
    brand: BrandConfig = BrandConfig()
    character: CharacterConfig = CharacterConfig()
    voice: VoiceConfig = VoiceConfig()
    footage: FootageConfig = FootageConfig()
    video: VideoConfig = VideoConfig()
    carousel: CarouselConfig = CarouselConfig()
    llm: LLMConfig = LLMConfig()
    notion: NotionConfig = NotionConfig()
    metricool: MetricoolConfig = MetricoolConfig()
    output_dir: str = "soul-studio/output"
    state_file: str = "soul-studio/state/processed.json"
    fonts_dir: str = "soul-studio/assets/fonts"
    prompts_dir: str = "soul-studio/prompts"

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

    @property
    def elevenlabs_api_key(self) -> str:
        return os.environ.get("ELEVENLABS_API_KEY", "")


def load_settings(config_path: Path | None = None) -> Settings:
    _load_dotenv(ROOT / ".env")
    _load_dotenv(REPO_ROOT / ".env")
    path = config_path or Path(os.environ.get("SOUL_STUDIO_CONFIG", ROOT / "config.yaml"))
    data: dict = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = Settings.model_validate(data)
    if os.environ.get("ELEVENLABS_VOICE_ID"):
        settings.voice.elevenlabs_voice_id = os.environ["ELEVENLABS_VOICE_ID"]
    for var in ("CHARACTER_PHOTOS", "CHARACTER_PHOTO_URL"):
        if os.environ.get(var):
            settings.character.photos = [u.strip() for u in os.environ[var].split(",") if u.strip()]
    if os.environ.get("VIDEO_MODE"):
        settings.video.mode = os.environ["VIDEO_MODE"]  # type: ignore[assignment]
    if os.environ.get("FOOTAGE_PROVIDER"):
        settings.footage.provider = os.environ["FOOTAGE_PROVIDER"]  # type: ignore[assignment]
    if os.environ.get("SOUL_STUDIO_LLM_MODEL"):
        settings.llm.model = os.environ["SOUL_STUDIO_LLM_MODEL"]
    return settings
