import asyncio
import base64
import io
import json
import logging
import mimetypes
import re
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from open_webui.config import CACHE_DIR
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import ENABLE_FORWARD_USER_INFO_HEADERS, SRC_LOG_LEVELS
from open_webui.routers.files import upload_file
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.images.comfyui import (
    ComfyUIGenerateImageForm,
    ComfyUIWorkflow,
    comfyui_generate_image,
)
from pydantic import BaseModel

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["IMAGES"])

IMAGE_CACHE_DIR = CACHE_DIR / "image" / "generations"
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


router = APIRouter()


@router.get("/config")
async def get_config(request: Request, user=Depends(get_admin_user)):
    return {
        "enabled": request.app.state.config.ENABLE_IMAGE_GENERATION,
        "engine": request.app.state.config.IMAGE_GENERATION_ENGINE,
        "prompt_generation": request.app.state.config.ENABLE_IMAGE_PROMPT_GENERATION,
        "openai": {
            "OPENAI_API_BASE_URL": request.app.state.config.IMAGES_OPENAI_API_BASE_URL,
            "OPENAI_API_KEY": request.app.state.config.IMAGES_OPENAI_API_KEY,
        },
        "automatic1111": {
            "AUTOMATIC1111_BASE_URL": request.app.state.config.AUTOMATIC1111_BASE_URL,
            "AUTOMATIC1111_API_AUTH": request.app.state.config.AUTOMATIC1111_API_AUTH,
            "AUTOMATIC1111_CFG_SCALE": request.app.state.config.AUTOMATIC1111_CFG_SCALE,
            "AUTOMATIC1111_SAMPLER": request.app.state.config.AUTOMATIC1111_SAMPLER,
            "AUTOMATIC1111_SCHEDULER": request.app.state.config.AUTOMATIC1111_SCHEDULER,
            "AUTOMATIC1111_SEED": request.app.state.config.AUTOMATIC1111_SEED,
            "AUTOMATIC1111_CLIP_SKIP": request.app.state.config.AUTOMATIC1111_CLIP_SKIP,
            "AUTOMATIC1111_VAE": request.app.state.config.AUTOMATIC1111_VAE,
            "AUTOMATIC1111_ENABLE_HR": request.app.state.config.AUTOMATIC1111_ENABLE_HR,
            "AUTOMATIC1111_HR_SCALE": request.app.state.config.AUTOMATIC1111_HR_SCALE,
            "AUTOMATIC1111_HR_UPSCALER": request.app.state.config.AUTOMATIC1111_HR_UPSCALER,
            "AUTOMATIC1111_DENOISING_STRENGTH": request.app.state.config.AUTOMATIC1111_DENOISING_STRENGTH,
            "AUTOMATIC1111_BATCH_COUNT": request.app.state.config.AUTOMATIC1111_BATCH_COUNT,
            "AUTOMATIC1111_RESTORE_FACES": request.app.state.config.AUTOMATIC1111_RESTORE_FACES,
            "AUTOMATIC1111_TILING": request.app.state.config.AUTOMATIC1111_TILING,
            "AUTOMATIC1111_LORAS": request.app.state.config.AUTOMATIC1111_LORAS,
            "AUTOMATIC1111_PROMPT_GENERATION_MODEL": request.app.state.config.AUTOMATIC1111_PROMPT_GENERATION_MODEL,
        },
        "comfyui": {
            "COMFYUI_BASE_URL": request.app.state.config.COMFYUI_BASE_URL,
            "COMFYUI_API_KEY": request.app.state.config.COMFYUI_API_KEY,
            "COMFYUI_WORKFLOW": request.app.state.config.COMFYUI_WORKFLOW,
            "COMFYUI_WORKFLOW_NODES": request.app.state.config.COMFYUI_WORKFLOW_NODES,
        },
        "gemini": {
            "GEMINI_API_BASE_URL": request.app.state.config.IMAGES_GEMINI_API_BASE_URL,
            "GEMINI_API_KEY": request.app.state.config.IMAGES_GEMINI_API_KEY,
        },
    }


class OpenAIConfigForm(BaseModel):
    OPENAI_API_BASE_URL: str
    OPENAI_API_KEY: str


class Automatic1111LoraConfig(BaseModel):
    name: str
    weight: float = 1.0


class Automatic1111ConfigForm(BaseModel):
    AUTOMATIC1111_BASE_URL: str
    AUTOMATIC1111_API_AUTH: str
    AUTOMATIC1111_CFG_SCALE: Optional[str | float | int]
    AUTOMATIC1111_SAMPLER: Optional[str]
    AUTOMATIC1111_SCHEDULER: Optional[str]
    AUTOMATIC1111_SEED: Optional[int] = -1
    AUTOMATIC1111_CLIP_SKIP: Optional[int]
    AUTOMATIC1111_VAE: Optional[str] = ""
    AUTOMATIC1111_ENABLE_HR: Optional[bool] = False
    AUTOMATIC1111_HR_SCALE: Optional[float] = 2.0
    AUTOMATIC1111_HR_UPSCALER: Optional[str] = "Latent"
    AUTOMATIC1111_DENOISING_STRENGTH: Optional[float] = 0.7
    AUTOMATIC1111_BATCH_COUNT: Optional[int] = 1
    AUTOMATIC1111_RESTORE_FACES: Optional[bool] = False
    AUTOMATIC1111_TILING: Optional[bool] = False
    AUTOMATIC1111_LORAS: Optional[list[dict]] = []
    AUTOMATIC1111_PROMPT_GENERATION_MODEL: Optional[str] = ""


class ComfyUIConfigForm(BaseModel):
    COMFYUI_BASE_URL: str
    COMFYUI_API_KEY: str
    COMFYUI_WORKFLOW: str
    COMFYUI_WORKFLOW_NODES: list[dict]


class GeminiConfigForm(BaseModel):
    GEMINI_API_BASE_URL: str
    GEMINI_API_KEY: str


class ConfigForm(BaseModel):
    enabled: bool
    engine: str
    prompt_generation: bool
    openai: OpenAIConfigForm
    automatic1111: Automatic1111ConfigForm
    comfyui: ComfyUIConfigForm
    gemini: GeminiConfigForm


@router.post("/config/update")
async def update_config(
    request: Request, form_data: ConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.IMAGE_GENERATION_ENGINE = form_data.engine
    request.app.state.config.ENABLE_IMAGE_GENERATION = form_data.enabled

    request.app.state.config.ENABLE_IMAGE_PROMPT_GENERATION = (
        form_data.prompt_generation
    )

    request.app.state.config.IMAGES_OPENAI_API_BASE_URL = (
        form_data.openai.OPENAI_API_BASE_URL
    )
    request.app.state.config.IMAGES_OPENAI_API_KEY = form_data.openai.OPENAI_API_KEY

    request.app.state.config.IMAGES_GEMINI_API_BASE_URL = (
        form_data.gemini.GEMINI_API_BASE_URL
    )
    request.app.state.config.IMAGES_GEMINI_API_KEY = form_data.gemini.GEMINI_API_KEY

    request.app.state.config.AUTOMATIC1111_BASE_URL = (
        form_data.automatic1111.AUTOMATIC1111_BASE_URL
    )
    request.app.state.config.AUTOMATIC1111_API_AUTH = (
        form_data.automatic1111.AUTOMATIC1111_API_AUTH
    )

    request.app.state.config.AUTOMATIC1111_CFG_SCALE = (
        float(form_data.automatic1111.AUTOMATIC1111_CFG_SCALE)
        if form_data.automatic1111.AUTOMATIC1111_CFG_SCALE
        else None
    )
    request.app.state.config.AUTOMATIC1111_SAMPLER = (
        form_data.automatic1111.AUTOMATIC1111_SAMPLER
        if form_data.automatic1111.AUTOMATIC1111_SAMPLER
        else None
    )
    request.app.state.config.AUTOMATIC1111_SCHEDULER = (
        form_data.automatic1111.AUTOMATIC1111_SCHEDULER
        if form_data.automatic1111.AUTOMATIC1111_SCHEDULER
        else None
    )

    # Additional AUTOMATIC1111 settings
    request.app.state.config.AUTOMATIC1111_SEED = (
        form_data.automatic1111.AUTOMATIC1111_SEED
        if form_data.automatic1111.AUTOMATIC1111_SEED is not None
        else -1
    )
    request.app.state.config.AUTOMATIC1111_CLIP_SKIP = (
        form_data.automatic1111.AUTOMATIC1111_CLIP_SKIP
        if form_data.automatic1111.AUTOMATIC1111_CLIP_SKIP
        else None
    )
    request.app.state.config.AUTOMATIC1111_VAE = (
        form_data.automatic1111.AUTOMATIC1111_VAE or ""
    )
    request.app.state.config.AUTOMATIC1111_ENABLE_HR = (
        form_data.automatic1111.AUTOMATIC1111_ENABLE_HR or False
    )
    request.app.state.config.AUTOMATIC1111_HR_SCALE = (
        form_data.automatic1111.AUTOMATIC1111_HR_SCALE or 2.0
    )
    request.app.state.config.AUTOMATIC1111_HR_UPSCALER = (
        form_data.automatic1111.AUTOMATIC1111_HR_UPSCALER or "Latent"
    )
    request.app.state.config.AUTOMATIC1111_DENOISING_STRENGTH = (
        form_data.automatic1111.AUTOMATIC1111_DENOISING_STRENGTH or 0.7
    )
    request.app.state.config.AUTOMATIC1111_BATCH_COUNT = (
        form_data.automatic1111.AUTOMATIC1111_BATCH_COUNT or 1
    )
    request.app.state.config.AUTOMATIC1111_RESTORE_FACES = (
        form_data.automatic1111.AUTOMATIC1111_RESTORE_FACES or False
    )
    request.app.state.config.AUTOMATIC1111_TILING = (
        form_data.automatic1111.AUTOMATIC1111_TILING or False
    )
    request.app.state.config.AUTOMATIC1111_LORAS = (
        form_data.automatic1111.AUTOMATIC1111_LORAS or []
    )
    request.app.state.config.AUTOMATIC1111_PROMPT_GENERATION_MODEL = (
        form_data.automatic1111.AUTOMATIC1111_PROMPT_GENERATION_MODEL or ""
    )

    request.app.state.config.COMFYUI_BASE_URL = (
        form_data.comfyui.COMFYUI_BASE_URL.strip("/")
    )
    request.app.state.config.COMFYUI_API_KEY = form_data.comfyui.COMFYUI_API_KEY

    request.app.state.config.COMFYUI_WORKFLOW = form_data.comfyui.COMFYUI_WORKFLOW
    request.app.state.config.COMFYUI_WORKFLOW_NODES = (
        form_data.comfyui.COMFYUI_WORKFLOW_NODES
    )

    return {
        "enabled": request.app.state.config.ENABLE_IMAGE_GENERATION,
        "engine": request.app.state.config.IMAGE_GENERATION_ENGINE,
        "prompt_generation": request.app.state.config.ENABLE_IMAGE_PROMPT_GENERATION,
        "openai": {
            "OPENAI_API_BASE_URL": request.app.state.config.IMAGES_OPENAI_API_BASE_URL,
            "OPENAI_API_KEY": request.app.state.config.IMAGES_OPENAI_API_KEY,
        },
        "automatic1111": {
            "AUTOMATIC1111_BASE_URL": request.app.state.config.AUTOMATIC1111_BASE_URL,
            "AUTOMATIC1111_API_AUTH": request.app.state.config.AUTOMATIC1111_API_AUTH,
            "AUTOMATIC1111_CFG_SCALE": request.app.state.config.AUTOMATIC1111_CFG_SCALE,
            "AUTOMATIC1111_SAMPLER": request.app.state.config.AUTOMATIC1111_SAMPLER,
            "AUTOMATIC1111_SCHEDULER": request.app.state.config.AUTOMATIC1111_SCHEDULER,
            "AUTOMATIC1111_SEED": request.app.state.config.AUTOMATIC1111_SEED,
            "AUTOMATIC1111_CLIP_SKIP": request.app.state.config.AUTOMATIC1111_CLIP_SKIP,
            "AUTOMATIC1111_VAE": request.app.state.config.AUTOMATIC1111_VAE,
            "AUTOMATIC1111_ENABLE_HR": request.app.state.config.AUTOMATIC1111_ENABLE_HR,
            "AUTOMATIC1111_HR_SCALE": request.app.state.config.AUTOMATIC1111_HR_SCALE,
            "AUTOMATIC1111_HR_UPSCALER": request.app.state.config.AUTOMATIC1111_HR_UPSCALER,
            "AUTOMATIC1111_DENOISING_STRENGTH": request.app.state.config.AUTOMATIC1111_DENOISING_STRENGTH,
            "AUTOMATIC1111_BATCH_COUNT": request.app.state.config.AUTOMATIC1111_BATCH_COUNT,
            "AUTOMATIC1111_RESTORE_FACES": request.app.state.config.AUTOMATIC1111_RESTORE_FACES,
            "AUTOMATIC1111_TILING": request.app.state.config.AUTOMATIC1111_TILING,
            "AUTOMATIC1111_LORAS": request.app.state.config.AUTOMATIC1111_LORAS,
            "AUTOMATIC1111_PROMPT_GENERATION_MODEL": request.app.state.config.AUTOMATIC1111_PROMPT_GENERATION_MODEL,
        },
        "comfyui": {
            "COMFYUI_BASE_URL": request.app.state.config.COMFYUI_BASE_URL,
            "COMFYUI_API_KEY": request.app.state.config.COMFYUI_API_KEY,
            "COMFYUI_WORKFLOW": request.app.state.config.COMFYUI_WORKFLOW,
            "COMFYUI_WORKFLOW_NODES": request.app.state.config.COMFYUI_WORKFLOW_NODES,
        },
        "gemini": {
            "GEMINI_API_BASE_URL": request.app.state.config.IMAGES_GEMINI_API_BASE_URL,
            "GEMINI_API_KEY": request.app.state.config.IMAGES_GEMINI_API_KEY,
        },
    }


def get_automatic1111_api_auth(request: Request):
    if request.app.state.config.AUTOMATIC1111_API_AUTH is None:
        return ""
    else:
        auth1111_byte_string = request.app.state.config.AUTOMATIC1111_API_AUTH.encode(
            "utf-8"
        )
        auth1111_base64_encoded_bytes = base64.b64encode(auth1111_byte_string)
        auth1111_base64_encoded_string = auth1111_base64_encoded_bytes.decode("utf-8")
        return f"Basic {auth1111_base64_encoded_string}"


@router.get("/config/url/verify")
async def verify_url(request: Request, user=Depends(get_admin_user)):
    if request.app.state.config.IMAGE_GENERATION_ENGINE == "automatic1111":
        try:
            r = requests.get(
                url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/options",
                headers={"authorization": get_automatic1111_api_auth(request)},
            )
            r.raise_for_status()
            return True
        except Exception:
            request.app.state.config.ENABLE_IMAGE_GENERATION = False
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES.INVALID_URL)
    elif request.app.state.config.IMAGE_GENERATION_ENGINE == "comfyui":

        headers = None
        if request.app.state.config.COMFYUI_API_KEY:
            headers = {
                "Authorization": f"Bearer {request.app.state.config.COMFYUI_API_KEY}"
            }

        try:
            r = requests.get(
                url=f"{request.app.state.config.COMFYUI_BASE_URL}/object_info",
                headers=headers,
            )
            r.raise_for_status()
            return True
        except Exception:
            request.app.state.config.ENABLE_IMAGE_GENERATION = False
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES.INVALID_URL)
    else:
        return True


def set_image_model(request: Request, model: str):
    log.info(f"Setting image model to {model}")
    request.app.state.config.IMAGE_GENERATION_MODEL = model
    if request.app.state.config.IMAGE_GENERATION_ENGINE in ["", "automatic1111"]:
        api_auth = get_automatic1111_api_auth(request)
        r = requests.get(
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/options",
            headers={"authorization": api_auth},
        )
        options = r.json()
        if model != options["sd_model_checkpoint"]:
            options["sd_model_checkpoint"] = model
            r = requests.post(
                url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/options",
                json=options,
                headers={"authorization": api_auth},
            )
    return request.app.state.config.IMAGE_GENERATION_MODEL


def get_image_model(request):
    if request.app.state.config.IMAGE_GENERATION_ENGINE == "openai":
        return (
            request.app.state.config.IMAGE_GENERATION_MODEL
            if request.app.state.config.IMAGE_GENERATION_MODEL
            else "dall-e-2"
        )
    elif request.app.state.config.IMAGE_GENERATION_ENGINE == "gemini":
        return (
            request.app.state.config.IMAGE_GENERATION_MODEL
            if request.app.state.config.IMAGE_GENERATION_MODEL
            else "imagen-3.0-generate-002"
        )
    elif request.app.state.config.IMAGE_GENERATION_ENGINE == "comfyui":
        return (
            request.app.state.config.IMAGE_GENERATION_MODEL
            if request.app.state.config.IMAGE_GENERATION_MODEL
            else ""
        )
    elif (
        request.app.state.config.IMAGE_GENERATION_ENGINE == "automatic1111"
        or request.app.state.config.IMAGE_GENERATION_ENGINE == ""
    ):
        try:
            r = requests.get(
                url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/options",
                headers={"authorization": get_automatic1111_api_auth(request)},
            )
            options = r.json()
            return options["sd_model_checkpoint"]
        except Exception as e:
            request.app.state.config.ENABLE_IMAGE_GENERATION = False
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


class ImageConfigForm(BaseModel):
    MODEL: str
    IMAGE_SIZE: str
    IMAGE_STEPS: int


@router.get("/image/config")
async def get_image_config(request: Request, user=Depends(get_admin_user)):
    return {
        "MODEL": request.app.state.config.IMAGE_GENERATION_MODEL,
        "IMAGE_SIZE": request.app.state.config.IMAGE_SIZE,
        "IMAGE_STEPS": request.app.state.config.IMAGE_STEPS,
    }


@router.post("/image/config/update")
async def update_image_config(
    request: Request, form_data: ImageConfigForm, user=Depends(get_admin_user)
):
    set_image_model(request, form_data.MODEL)

    pattern = r"^\d+x\d+$"
    if re.match(pattern, form_data.IMAGE_SIZE):
        request.app.state.config.IMAGE_SIZE = form_data.IMAGE_SIZE
    else:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.INCORRECT_FORMAT("  (e.g., 512x512)."),
        )

    if form_data.IMAGE_STEPS >= 0:
        request.app.state.config.IMAGE_STEPS = form_data.IMAGE_STEPS
    else:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.INCORRECT_FORMAT("  (e.g., 50)."),
        )

    return {
        "MODEL": request.app.state.config.IMAGE_GENERATION_MODEL,
        "IMAGE_SIZE": request.app.state.config.IMAGE_SIZE,
        "IMAGE_STEPS": request.app.state.config.IMAGE_STEPS,
    }


@router.get("/models")
def get_models(request: Request, user=Depends(get_verified_user)):
    try:
        if request.app.state.config.IMAGE_GENERATION_ENGINE == "openai":
            return [
                {"id": "dall-e-2", "name": "DALL·E 2"},
                {"id": "dall-e-3", "name": "DALL·E 3"},
                {"id": "gpt-image-1", "name": "GPT-IMAGE 1"},
            ]
        elif request.app.state.config.IMAGE_GENERATION_ENGINE == "gemini":
            return [
                {"id": "imagen-3.0-generate-002", "name": "imagen-3.0 generate-002"},
            ]
        elif request.app.state.config.IMAGE_GENERATION_ENGINE == "comfyui":
            # TODO - get models from comfyui
            headers = {
                "Authorization": f"Bearer {request.app.state.config.COMFYUI_API_KEY}"
            }
            r = requests.get(
                url=f"{request.app.state.config.COMFYUI_BASE_URL}/object_info",
                headers=headers,
            )
            info = r.json()

            workflow = json.loads(request.app.state.config.COMFYUI_WORKFLOW)
            model_node_id = None

            for node in request.app.state.config.COMFYUI_WORKFLOW_NODES:
                if node["type"] == "model":
                    if node["node_ids"]:
                        model_node_id = node["node_ids"][0]
                    break

            if model_node_id:
                model_list_key = None

                log.info(workflow[model_node_id]["class_type"])
                for key in info[workflow[model_node_id]["class_type"]]["input"][
                    "required"
                ]:
                    if "_name" in key:
                        model_list_key = key
                        break

                if model_list_key:
                    return list(
                        map(
                            lambda model: {"id": model, "name": model},
                            info[workflow[model_node_id]["class_type"]]["input"][
                                "required"
                            ][model_list_key][0],
                        )
                    )
            else:
                return list(
                    map(
                        lambda model: {"id": model, "name": model},
                        info["CheckpointLoaderSimple"]["input"]["required"][
                            "ckpt_name"
                        ][0],
                    )
                )
        elif (
            request.app.state.config.IMAGE_GENERATION_ENGINE == "automatic1111"
            or request.app.state.config.IMAGE_GENERATION_ENGINE == ""
        ):
            r = requests.get(
                url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/sd-models",
                headers={"authorization": get_automatic1111_api_auth(request)},
            )
            models = r.json()
            return list(
                map(
                    lambda model: {"id": model["title"], "name": model["model_name"]},
                    models,
                )
            )
    except Exception as e:
        request.app.state.config.ENABLE_IMAGE_GENERATION = False
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


class LLMGeneratedSettings(BaseModel):
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None
    sampler_name: Optional[str] = None
    scheduler: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None
    enable_hr: Optional[bool] = None
    hr_scale: Optional[float] = None
    denoising_strength: Optional[float] = None
    restore_faces: Optional[bool] = None
    clip_skip: Optional[int] = None


class GenerateImageForm(BaseModel):
    model: Optional[str] = None
    prompt: str
    size: Optional[str] = None
    n: int = 1
    negative_prompt: Optional[str] = None
    settings: Optional[LLMGeneratedSettings] = None


def load_b64_image_data(b64_str):
    try:
        if "," in b64_str:
            header, encoded = b64_str.split(",", 1)
            mime_type = header.split(";")[0].lstrip("data:")
            img_data = base64.b64decode(encoded)
        else:
            mime_type = "image/png"
            img_data = base64.b64decode(b64_str)
        return img_data, mime_type
    except Exception as e:
        log.exception(f"Error loading image data: {e}")
        return None, None


def load_url_image_data(url, headers=None):
    try:
        if headers:
            r = requests.get(url, headers=headers)
        else:
            r = requests.get(url)

        r.raise_for_status()
        if r.headers["content-type"].split("/")[0] == "image":
            mime_type = r.headers["content-type"]
            return r.content, mime_type
        else:
            log.error("Url does not point to an image.")
            return None

    except Exception as e:
        log.exception(f"Error saving image: {e}")
        return None


def upload_image(request, image_data, content_type, metadata, user):
    image_format = mimetypes.guess_extension(content_type)
    file = UploadFile(
        file=io.BytesIO(image_data),
        filename=f"generated-image{image_format}",  # will be converted to a unique ID on upload_file
        headers={
            "content-type": content_type,
        },
    )
    file_item = upload_file(request, file, metadata=metadata, internal=True, user=user)
    url = request.app.url_path_for("get_file_content_by_id", id=file_item.id)
    return url


async def generate_prompt_with_llm(request: Request, prompt: str, user) -> dict:
    """
    Use Ollama LLM to generate English prompt and optimal settings for Stable Diffusion.
    Returns dict with 'prompt', 'negative_prompt', and 'settings'.
    """
    model = request.app.state.config.AUTOMATIC1111_PROMPT_GENERATION_MODEL
    if not model:
        return None

    try:
        from open_webui.config import DEFAULT_IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE

        # Check for trigger keywords for Custom Mode
        custom_keywords = [
            "background", "scenery", "landscape", "factory", "room", "interior", "exterior", "배경", "풍경",
            "character", "girl", "boy", "woman", "man", "person", "solo", "캐릭터", "인물", "소녀", "소년",
            "draw", "create", "generate", "make", "그려줘", "만들어줘", "생성해줘", "그림", "이미지"
        ]
        
        is_custom_request = any(k in prompt.lower() for k in custom_keywords)

        if is_custom_request:
            # Custom System Prompt for Dynamic Model/LoRA Selection
            system_prompt = f"""You are an expert Stable Diffusion prompt generator.
Analyze the user's request and determine if it is a CHARACTER-focused image or a BACKGROUND/SCENERY-focused image.

RULES:
1. IF the request is for a CHARACTER (person, girl, boy, etc.):
   - Use Model: "animagineXLV31_v31.safetensors"
   - Use LoRA: "<lora:sketch style:0.8>"
   - Add Style Keywords: "(masterpiece, best quality, very aesthetic, absrdres), newest, safe, (monochrome, greyscale:0.3), (rough sketch, messy lineart, traditional media, graphite:1.3)"
   - Use Negative Prompt: "nsfw, (low quality, worst quality:1.4), (photorealistic, realistic, 3d, render, blender:1.5), oil painting, heavy coloring, complex background, colorful, bad anatomy, bad hands, missing fingers, extra digits, blurry, jpeg artifacts, signature, watermark"

2. IF the request is for a BACKGROUND/SCENERY (place, landscape, room, etc.):
   - Use Model: "revAnimated_v2Rebirth.safetensors"
   - Use LoRA: "<lora:厚涂油画:1.0>"
   - Add Style Keywords: "(Masterpiece), digital concept art, atmospheric volumetric lighting, dusty air, thick oil painting brushstrokes, palette knife texture, gloomy industrial atmosphere, by Dishonored artists"
   - Use Negative Prompt: "nsfw, low quality, worst quality, text, watermark"

3. Translate the user's non-English request to English if necessary.

OUTPUT FORMAT (JSON ONLY):
{{
  "prompt": "Full generated prompt including style keywords and LoRA tag",
  "negative_prompt": "The specific negative prompt defined above",
  "model": "The specific model filename defined above",
  "settings": {{
      "steps": 30,
      "cfg_scale": 7.0,
      "sampler_name": "DPM++ 2M Karras",
      "width": 512,
      "height": 768
  }}
}}

User request: {prompt}"""
        else:
            # Fallback to Default System Prompt for general requests
            system_prompt = DEFAULT_IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE.replace(
                "{{MESSAGES:END:6}}",
                f"User request: {prompt}"
            )

        # Call Ollama
        ollama_base_urls = request.app.state.config.OLLAMA_BASE_URLS
        ollama_url = ollama_base_urls[0] if ollama_base_urls else "http://localhost:11434"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": system_prompt}],
            "stream": False,
            "format": "json"
        }

        r = await asyncio.to_thread(
            requests.post,
            url=f"{ollama_url}/api/chat",
            json=payload,
            timeout=60
        )

        if r.status_code == 200:
            result = r.json()
            content = result.get("message", {}).get("content", "")

            # Parse JSON response
            try:
                # Attempt to extract JSON if it's wrapped in markdown or mixed with text
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx : end_idx + 1]

                parsed = json.loads(content)
                log.info(f"LLM generated prompt and settings: {json.dumps(parsed, indent=2)}")
                return parsed
            except json.JSONDecodeError:
                log.warning(f"Failed to parse LLM response as JSON: {content}")
                return None
        else:
            log.warning(f"LLM call failed with status {r.status_code}")
            return None

    except Exception as e:
        log.error(f"Error generating prompt with LLM: {e}")
        return None


@router.post("/generations")
async def image_generations(
    request: Request,
    form_data: GenerateImageForm,
    user=Depends(get_verified_user),
):
    width, height = tuple(map(int, request.app.state.config.IMAGE_SIZE.split("x")))

    # If prompt generation model is set, use LLM to generate English prompt and settings
    llm_result = None
    if (request.app.state.config.IMAGE_GENERATION_ENGINE == "automatic1111" or
        request.app.state.config.IMAGE_GENERATION_ENGINE == ""):
        if request.app.state.config.AUTOMATIC1111_PROMPT_GENERATION_MODEL:
            llm_result = await generate_prompt_with_llm(request, form_data.prompt, user)
            if llm_result:
                # Override prompt with LLM-generated English prompt
                form_data.prompt = llm_result.get("prompt", form_data.prompt)
                if llm_result.get("negative_prompt"):
                    form_data.negative_prompt = llm_result.get("negative_prompt")
                
                # Copy model from LLM result if provided
                if llm_result.get("model"):
                    form_data.model = llm_result.get("model")

                # Create settings from LLM result
                if llm_result.get("settings"):
                    settings_dict = llm_result["settings"]
                    form_data.settings = LLMGeneratedSettings(
                        steps=settings_dict.get("steps"),
                        cfg_scale=settings_dict.get("cfg_scale"),
                        sampler_name=settings_dict.get("sampler_name"),
                        scheduler=settings_dict.get("scheduler"),
                        width=settings_dict.get("width"),
                        height=settings_dict.get("height"),
                        seed=settings_dict.get("seed"),
                        enable_hr=settings_dict.get("enable_hr"),
                        hr_scale=settings_dict.get("hr_scale"),
                        denoising_strength=settings_dict.get("denoising_strength"),
                        restore_faces=settings_dict.get("restore_faces"),
                        clip_skip=settings_dict.get("clip_skip")
                    )

    r = None
    try:
        if request.app.state.config.IMAGE_GENERATION_ENGINE == "openai":
            headers = {}
            headers["Authorization"] = (
                f"Bearer {request.app.state.config.IMAGES_OPENAI_API_KEY}"
            )
            headers["Content-Type"] = "application/json"

            if ENABLE_FORWARD_USER_INFO_HEADERS:
                headers["X-OpenWebUI-User-Name"] = user.name
                headers["X-OpenWebUI-User-Id"] = user.id
                headers["X-OpenWebUI-User-Email"] = user.email
                headers["X-OpenWebUI-User-Role"] = user.role

            data = {
                "model": (
                    request.app.state.config.IMAGE_GENERATION_MODEL
                    if request.app.state.config.IMAGE_GENERATION_MODEL != ""
                    else "dall-e-2"
                ),
                "prompt": form_data.prompt,
                "n": form_data.n,
                "size": (
                    form_data.size
                    if form_data.size
                    else request.app.state.config.IMAGE_SIZE
                ),
                **(
                    {}
                    if "gpt-image-1" in request.app.state.config.IMAGE_GENERATION_MODEL
                    else {"response_format": "b64_json"}
                ),
            }

            # Use asyncio.to_thread for the requests.post call
            r = await asyncio.to_thread(
                requests.post,
                url=f"{request.app.state.config.IMAGES_OPENAI_API_BASE_URL}/images/generations",
                json=data,
                headers=headers,
            )

            r.raise_for_status()
            res = r.json()

            images = []

            for image in res["data"]:
                if image_url := image.get("url", None):
                    image_data, content_type = load_url_image_data(image_url, headers)
                else:
                    image_data, content_type = load_b64_image_data(image["b64_json"])

                url = upload_image(request, image_data, content_type, data, user)
                images.append({"url": url})
            return images

        elif request.app.state.config.IMAGE_GENERATION_ENGINE == "gemini":
            headers = {}
            headers["Content-Type"] = "application/json"
            headers["x-goog-api-key"] = request.app.state.config.IMAGES_GEMINI_API_KEY

            model = get_image_model(request)
            data = {
                "instances": {"prompt": form_data.prompt},
                "parameters": {
                    "sampleCount": form_data.n,
                    "outputOptions": {"mimeType": "image/png"},
                },
            }

            # Use asyncio.to_thread for the requests.post call
            r = await asyncio.to_thread(
                requests.post,
                url=f"{request.app.state.config.IMAGES_GEMINI_API_BASE_URL}/models/{model}:predict",
                json=data,
                headers=headers,
            )

            r.raise_for_status()
            res = r.json()

            images = []
            for image in res["predictions"]:
                image_data, content_type = load_b64_image_data(
                    image["bytesBase64Encoded"]
                )
                url = upload_image(request, image_data, content_type, data, user)
                images.append({"url": url})

            return images

        elif request.app.state.config.IMAGE_GENERATION_ENGINE == "comfyui":
            data = {
                "prompt": form_data.prompt,
                "width": width,
                "height": height,
                "n": form_data.n,
            }

            if request.app.state.config.IMAGE_STEPS is not None:
                data["steps"] = request.app.state.config.IMAGE_STEPS

            if form_data.negative_prompt is not None:
                data["negative_prompt"] = form_data.negative_prompt

            form_data = ComfyUIGenerateImageForm(
                **{
                    "workflow": ComfyUIWorkflow(
                        **{
                            "workflow": request.app.state.config.COMFYUI_WORKFLOW,
                            "nodes": request.app.state.config.COMFYUI_WORKFLOW_NODES,
                        }
                    ),
                    **data,
                }
            )
            res = await comfyui_generate_image(
                request.app.state.config.IMAGE_GENERATION_MODEL,
                form_data,
                user.id,
                request.app.state.config.COMFYUI_BASE_URL,
                request.app.state.config.COMFYUI_API_KEY,
            )
            log.debug(f"res: {res}")

            images = []

            for image in res["data"]:
                headers = None
                if request.app.state.config.COMFYUI_API_KEY:
                    headers = {
                        "Authorization": f"Bearer {request.app.state.config.COMFYUI_API_KEY}"
                    }

                image_data, content_type = load_url_image_data(image["url"], headers)
                url = upload_image(
                    request,
                    image_data,
                    content_type,
                    form_data.model_dump(exclude_none=True),
                    user,
                )
                images.append({"url": url})
            return images
        elif (
            request.app.state.config.IMAGE_GENERATION_ENGINE == "automatic1111"
            or request.app.state.config.IMAGE_GENERATION_ENGINE == ""
        ):
            if form_data.model:
                set_image_model(request, form_data.model)

            # Get LLM-generated settings if available
            llm_settings = form_data.settings

            # Build prompt with configured LoRAs
            prompt = form_data.prompt
            if request.app.state.config.AUTOMATIC1111_LORAS:
                for lora in request.app.state.config.AUTOMATIC1111_LORAS:
                    lora_name = lora.get("name", "")
                    lora_weight = lora.get("weight", 1.0)
                    if lora_name:
                        prompt += f" <lora:{lora_name}:{lora_weight}>"

            # Use LLM settings if available, otherwise use config settings
            # Width and height from LLM or default config
            img_width = width
            img_height = height
            if llm_settings:
                if llm_settings.width:
                    img_width = llm_settings.width
                if llm_settings.height:
                    img_height = llm_settings.height

            data = {
                "prompt": prompt,
                "batch_size": form_data.n,
                "width": img_width,
                "height": img_height,
            }

            # Steps: LLM > config
            if llm_settings and llm_settings.steps:
                data["steps"] = llm_settings.steps
            elif request.app.state.config.IMAGE_STEPS is not None:
                data["steps"] = request.app.state.config.IMAGE_STEPS

            if form_data.negative_prompt is not None:
                data["negative_prompt"] = form_data.negative_prompt

            # CFG Scale: LLM > config
            if llm_settings and llm_settings.cfg_scale:
                data["cfg_scale"] = llm_settings.cfg_scale
            elif request.app.state.config.AUTOMATIC1111_CFG_SCALE:
                data["cfg_scale"] = request.app.state.config.AUTOMATIC1111_CFG_SCALE

            # Sampler: LLM > config
            if llm_settings and llm_settings.sampler_name:
                data["sampler_name"] = llm_settings.sampler_name
            elif request.app.state.config.AUTOMATIC1111_SAMPLER:
                data["sampler_name"] = request.app.state.config.AUTOMATIC1111_SAMPLER

            # Scheduler: LLM > config
            if llm_settings and llm_settings.scheduler:
                data["scheduler"] = llm_settings.scheduler
            elif request.app.state.config.AUTOMATIC1111_SCHEDULER:
                data["scheduler"] = request.app.state.config.AUTOMATIC1111_SCHEDULER

            # Seed: LLM > config
            if llm_settings and llm_settings.seed is not None:
                data["seed"] = llm_settings.seed
            elif request.app.state.config.AUTOMATIC1111_SEED is not None:
                data["seed"] = request.app.state.config.AUTOMATIC1111_SEED

            # Batch count
            if request.app.state.config.AUTOMATIC1111_BATCH_COUNT:
                data["n_iter"] = request.app.state.config.AUTOMATIC1111_BATCH_COUNT

            # Hires fix: LLM > config
            enable_hr = False
            if llm_settings and llm_settings.enable_hr:
                enable_hr = True
            elif request.app.state.config.AUTOMATIC1111_ENABLE_HR:
                enable_hr = True

            if enable_hr:
                data["enable_hr"] = True
                if llm_settings and llm_settings.hr_scale:
                    data["hr_scale"] = llm_settings.hr_scale
                else:
                    data["hr_scale"] = request.app.state.config.AUTOMATIC1111_HR_SCALE or 2.0
                data["hr_upscaler"] = request.app.state.config.AUTOMATIC1111_HR_UPSCALER or "Latent"
                if llm_settings and llm_settings.denoising_strength:
                    data["denoising_strength"] = llm_settings.denoising_strength
                else:
                    data["denoising_strength"] = request.app.state.config.AUTOMATIC1111_DENOISING_STRENGTH or 0.7

            # Restore faces: LLM > config
            if llm_settings and llm_settings.restore_faces:
                data["restore_faces"] = True
            elif request.app.state.config.AUTOMATIC1111_RESTORE_FACES:
                data["restore_faces"] = True

            # Tiling
            if request.app.state.config.AUTOMATIC1111_TILING:
                data["tiling"] = True

            # Override settings (VAE, CLIP skip)
            override_settings = {}

            # CLIP skip: LLM > config
            if llm_settings and llm_settings.clip_skip:
                override_settings["CLIP_stop_at_last_layers"] = llm_settings.clip_skip
            elif request.app.state.config.AUTOMATIC1111_CLIP_SKIP:
                override_settings["CLIP_stop_at_last_layers"] = request.app.state.config.AUTOMATIC1111_CLIP_SKIP

            if request.app.state.config.AUTOMATIC1111_VAE:
                override_settings["sd_vae"] = request.app.state.config.AUTOMATIC1111_VAE

            if override_settings:
                data["override_settings"] = override_settings

            # Log if LLM settings were used
            if llm_settings:
                log.info(f"=== Using LLM-generated settings ===")
                log.info(f"LLM Settings: {llm_settings.model_dump(exclude_none=True)}")

            # Log the request data being sent to SD WebUI
            log.info(f"=== AUTOMATIC1111 Request Data ===")
            log.info(f"Prompt: {data.get('prompt', '')[:200]}...")
            log.info(f"Negative Prompt: {data.get('negative_prompt', '')[:100]}...")
            log.info(f"Size: {data.get('width')}x{data.get('height')}")
            log.info(f"Steps: {data.get('steps')}")
            log.info(f"CFG Scale: {data.get('cfg_scale')}")
            log.info(f"Sampler: {data.get('sampler_name')}")
            log.info(f"Scheduler: {data.get('scheduler')}")
            log.info(f"Seed: {data.get('seed')}")
            log.info(f"Batch Size: {data.get('batch_size')}, Batch Count: {data.get('n_iter')}")
            log.info(f"Hires Fix: {data.get('enable_hr', False)}")
            if data.get('enable_hr'):
                log.info(f"  HR Scale: {data.get('hr_scale')}, Upscaler: {data.get('hr_upscaler')}, Denoising: {data.get('denoising_strength')}")
            log.info(f"Restore Faces: {data.get('restore_faces', False)}")
            log.info(f"Tiling: {data.get('tiling', False)}")
            if data.get('override_settings'):
                log.info(f"Override Settings: {data.get('override_settings')}")
            log.info(f"=== Full Request JSON ===")
            log.info(f"{json.dumps(data, indent=2, default=str)}")

            # Use asyncio.to_thread for the requests.post call
            r = await asyncio.to_thread(
                requests.post,
                url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/txt2img",
                json=data,
                headers={"authorization": get_automatic1111_api_auth(request)},
            )

            res = r.json()
            log.debug(f"res: {res}")

            images = []

            for image in res["images"]:
                image_data, content_type = load_b64_image_data(image)
                url = upload_image(
                    request,
                    image_data,
                    content_type,
                    {**data, "info": res["info"]},
                    user,
                )
                images.append({"url": url, "prompt": data["prompt"]})
            return images
    except Exception as e:
        error = e
        if r != None:
            data = r.json()
            if "error" in data:
                error = data["error"]["message"]
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(error))


# Optimize Settings API
class OptimizeSettingsForm(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    current_settings: Optional[dict] = None


class OptimizedSettingsResponse(BaseModel):
    prompt: str
    negative_prompt: str
    steps: int
    cfg_scale: float
    sampler_name: str
    scheduler: str
    width: int
    height: int
    seed: int
    enable_hr: bool
    hr_scale: Optional[float] = None
    denoising_strength: Optional[float] = None
    restore_faces: bool
    clip_skip: int
    reasoning: str


@router.post("/optimize-settings")
async def optimize_settings(
    request: Request,
    form_data: OptimizeSettingsForm,
    user=Depends(get_verified_user),
):
    """Analyze prompt and suggest optimal generation settings"""
    try:
        model = request.app.state.config.AUTOMATIC1111_PROMPT_GENERATION_MODEL

        if not model:
            raise HTTPException(
                status_code=400,
                detail="No prompt generation model configured. Set AUTOMATIC1111_PROMPT_GENERATION_MODEL in settings."
            )

        # Build context about current settings
        current_settings_info = ""
        if form_data.current_settings:
            current_settings_info = f"\n\nCurrent settings: {json.dumps(form_data.current_settings)}"

        system_prompt = """You are an expert Stable Diffusion settings optimizer. Analyze the prompt and suggest optimal generation settings.

Consider these factors:
1. Content type (portrait, landscape, anime, photorealistic, abstract, etc.)
2. Detail level required
3. Style (artistic, photorealistic, anime, illustration)
4. Subject complexity

Guidelines:
- Portraits: Higher CFG (7-9), DPM++ 2M Karras, 512x768 or 768x1024, restore_faces=true
- Landscapes: Medium CFG (6-8), Euler a, 768x512 or 1024x768
- Anime: Lower CFG (5-7), DPM++ 2M SDE Karras, CLIP skip 2
- Photorealistic: Higher steps (30-50), CFG 7-8, DPM++ 2M Karras
- Abstract/Artistic: Higher CFG (8-12), varied samplers
- High detail: Enable hires fix with 1.5-2x scale
- Simple/quick: Lower steps (20-25), no hires fix

Respond ONLY in valid JSON:
{
    "prompt": "enhanced prompt with quality tags",
    "negative_prompt": "appropriate negative prompt",
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler_name": "DPM++ 2M",
    "scheduler": "Karras",
    "width": 512,
    "height": 768,
    "seed": -1,
    "enable_hr": false,
    "hr_scale": 2.0,
    "denoising_strength": 0.7,
    "restore_faces": false,
    "clip_skip": 1,
    "reasoning": "Brief explanation of why these settings were chosen"
}"""

        user_prompt = f"""Analyze and optimize settings for this prompt:

Prompt: {form_data.prompt}
Negative prompt: {form_data.negative_prompt or 'None provided'}{current_settings_info}

Provide optimized settings that will produce the best quality result for this specific content."""

        # Call Ollama API
        ollama_base_urls = request.app.state.config.OLLAMA_BASE_URLS
        ollama_base_url = ollama_base_urls[0] if ollama_base_urls else "http://localhost:11434"

        r = await asyncio.to_thread(
            requests.post,
            url=f"{ollama_base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "format": "json"
            },
        )
        r.raise_for_status()

        response = r.json()
        content = response.get("message", {}).get("content", "{}")

        try:
            result = json.loads(content)
            return OptimizedSettingsResponse(
                prompt=result.get("prompt", form_data.prompt),
                negative_prompt=result.get("negative_prompt", "low quality, blurry, deformed"),
                steps=result.get("steps", 30),
                cfg_scale=result.get("cfg_scale", 7.0),
                sampler_name=result.get("sampler_name", "DPM++ 2M"),
                scheduler=result.get("scheduler", "Karras"),
                width=result.get("width", 512),
                height=result.get("height", 512),
                seed=result.get("seed", -1),
                enable_hr=result.get("enable_hr", False),
                hr_scale=result.get("hr_scale"),
                denoising_strength=result.get("denoising_strength"),
                restore_faces=result.get("restore_faces", False),
                clip_skip=result.get("clip_skip", 1),
                reasoning=result.get("reasoning", "")
            )
        except json.JSONDecodeError:
            # Return defaults if parsing fails
            return OptimizedSettingsResponse(
                prompt=form_data.prompt,
                negative_prompt=form_data.negative_prompt or "low quality, blurry, deformed",
                steps=30,
                cfg_scale=7.0,
                sampler_name="DPM++ 2M",
                scheduler="Karras",
                width=512,
                height=512,
                seed=-1,
                enable_hr=False,
                restore_faces=False,
                clip_skip=1,
                reasoning="Could not parse LLM response, using defaults"
            )

    except Exception as e:
        log.exception(f"Error optimizing settings: {e}")
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


# SD WebUI Data Retrieval APIs
@router.get("/automatic1111/samplers")
async def get_automatic1111_samplers(request: Request, user=Depends(get_verified_user)):
    """Get list of available samplers from AUTOMATIC1111"""
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/samplers",
            headers={"authorization": get_automatic1111_api_auth(request)},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


@router.get("/automatic1111/schedulers")
async def get_automatic1111_schedulers(request: Request, user=Depends(get_verified_user)):
    """Get list of available schedulers from AUTOMATIC1111"""
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/schedulers",
            headers={"authorization": get_automatic1111_api_auth(request)},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


@router.get("/automatic1111/loras")
async def get_automatic1111_loras(request: Request, user=Depends(get_verified_user)):
    """Get list of available LoRAs from AUTOMATIC1111"""
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/loras",
            headers={"authorization": get_automatic1111_api_auth(request)},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


@router.get("/automatic1111/sd-vae")
async def get_automatic1111_vaes(request: Request, user=Depends(get_verified_user)):
    """Get list of available VAEs from AUTOMATIC1111"""
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/sd-vae",
            headers={"authorization": get_automatic1111_api_auth(request)},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


@router.get("/automatic1111/upscalers")
async def get_automatic1111_upscalers(request: Request, user=Depends(get_verified_user)):
    """Get list of available upscalers from AUTOMATIC1111"""
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/upscalers",
            headers={"authorization": get_automatic1111_api_auth(request)},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


@router.get("/automatic1111/embeddings")
async def get_automatic1111_embeddings(request: Request, user=Depends(get_verified_user)):
    """Get list of available embeddings (Textual Inversions) from AUTOMATIC1111"""
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/embeddings",
            headers={"authorization": get_automatic1111_api_auth(request)},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


@router.get("/automatic1111/options")
async def get_automatic1111_options(request: Request, user=Depends(get_admin_user)):
    """Get current options/settings from AUTOMATIC1111"""
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/options",
            headers={"authorization": get_automatic1111_api_auth(request)},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


@router.post("/automatic1111/refresh-loras")
async def refresh_automatic1111_loras(request: Request, user=Depends(get_verified_user)):
    """Refresh LoRA list in AUTOMATIC1111"""
    try:
        r = await asyncio.to_thread(
            requests.post,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/refresh-loras",
            headers={"authorization": get_automatic1111_api_auth(request)},
        )
        r.raise_for_status()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


# Ollama Prompt Generation API
class PromptGenerationForm(BaseModel):
    user_input: str
    model: Optional[str] = None
    available_loras: Optional[list[dict]] = None


class GeneratedPromptResponse(BaseModel):
    positive_prompt: str
    negative_prompt: str
    suggested_loras: list[dict] = []
    suggested_settings: dict = {}


@router.post("/generate-prompt")
async def generate_prompt_with_ollama(
    request: Request,
    form_data: PromptGenerationForm,
    user=Depends(get_verified_user),
):
    """Generate optimized SD prompts using Ollama LLM"""
    try:
        # Get the model to use for prompt generation
        model = form_data.model or request.app.state.config.AUTOMATIC1111_PROMPT_GENERATION_MODEL

        if not model:
            raise HTTPException(
                status_code=400,
                detail="No prompt generation model specified. Set AUTOMATIC1111_PROMPT_GENERATION_MODEL or provide model in request."
            )

        # Get available LoRAs info for the LLM
        loras_info = ""
        if form_data.available_loras:
            lora_names = [lora.get("name", lora.get("alias", "")) for lora in form_data.available_loras[:20]]
            loras_info = f"\n\nAvailable LoRAs: {', '.join(lora_names)}"

        # Create system prompt for Stable Diffusion prompt generation
        system_prompt = """You are an expert at creating Stable Diffusion image generation prompts.
Your task is to convert user descriptions into optimized prompts for Stable Diffusion.

Rules:
1. Create detailed, comma-separated positive prompts with quality tags (masterpiece, best quality, highly detailed, etc.)
2. Create appropriate negative prompts to avoid common issues (low quality, blurry, deformed, etc.)
3. If LoRAs are available and relevant, suggest them with appropriate weights (0.5-1.0)
4. Suggest optimal settings based on the content type

Respond ONLY in valid JSON format:
{
    "positive_prompt": "your detailed positive prompt here",
    "negative_prompt": "your negative prompt here",
    "suggested_loras": [{"name": "lora_name", "weight": 0.8}],
    "suggested_settings": {
        "steps": 30,
        "cfg_scale": 7,
        "sampler": "DPM++ 2M",
        "scheduler": "karras"
    }
}"""

        user_prompt = f"Create Stable Diffusion prompts for: {form_data.user_input}{loras_info}"

        # Call Ollama API
        ollama_base_url = request.app.state.config.OLLAMA_BASE_URL

        r = await asyncio.to_thread(
            requests.post,
            url=f"{ollama_base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "format": "json"
            },
        )
        r.raise_for_status()

        response = r.json()
        content = response.get("message", {}).get("content", "{}")

        # Parse JSON response
        try:
            result = json.loads(content)
            return GeneratedPromptResponse(
                positive_prompt=result.get("positive_prompt", form_data.user_input),
                negative_prompt=result.get("negative_prompt", "low quality, blurry, deformed"),
                suggested_loras=result.get("suggested_loras", []),
                suggested_settings=result.get("suggested_settings", {})
            )
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return GeneratedPromptResponse(
                positive_prompt=content if content else form_data.user_input,
                negative_prompt="low quality, blurry, deformed, bad anatomy",
                suggested_loras=[],
                suggested_settings={}
            )

    except Exception as e:
        log.exception(f"Error generating prompt with Ollama: {e}")
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


# Advanced Image Generation with all SD settings
class AdvancedGenerateImageForm(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    model: Optional[str] = None

    # Basic settings
    width: Optional[int] = None
    height: Optional[int] = None
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None
    seed: Optional[int] = -1
    batch_size: Optional[int] = 1
    batch_count: Optional[int] = 1

    # Sampler settings
    sampler_name: Optional[str] = None
    scheduler: Optional[str] = None

    # LoRA settings
    loras: Optional[list[dict]] = None  # [{"name": "lora_name", "weight": 1.0}]

    # Hires fix settings
    enable_hr: Optional[bool] = False
    hr_scale: Optional[float] = 2.0
    hr_upscaler: Optional[str] = "Latent"
    denoising_strength: Optional[float] = 0.7

    # Other settings
    restore_faces: Optional[bool] = False
    tiling: Optional[bool] = False

    # Override settings (VAE, CLIP skip, etc.)
    clip_skip: Optional[int] = None
    vae: Optional[str] = None


@router.post("/generations/advanced")
async def advanced_image_generations(
    request: Request,
    form_data: AdvancedGenerateImageForm,
    user=Depends(get_verified_user),
):
    """Generate images with all SD WebUI settings"""

    if request.app.state.config.IMAGE_GENERATION_ENGINE not in ["automatic1111", ""]:
        raise HTTPException(
            status_code=400,
            detail="Advanced generation is only available for AUTOMATIC1111 engine"
        )

    try:
        # Set model if specified
        if form_data.model:
            set_image_model(request, form_data.model)

        # Build prompt with LoRAs
        prompt = form_data.prompt
        if form_data.loras:
            for lora in form_data.loras:
                lora_name = lora.get("name", "")
                lora_weight = lora.get("weight", 1.0)
                if lora_name:
                    prompt += f" <lora:{lora_name}:{lora_weight}>"

        # Get default values from config
        width = form_data.width or int(request.app.state.config.IMAGE_SIZE.split("x")[0])
        height = form_data.height or int(request.app.state.config.IMAGE_SIZE.split("x")[1])

        # Build request data
        data = {
            "prompt": prompt,
            "negative_prompt": form_data.negative_prompt or "",
            "width": width,
            "height": height,
            "batch_size": form_data.batch_size or 1,
            "n_iter": form_data.batch_count or request.app.state.config.AUTOMATIC1111_BATCH_COUNT or 1,
            "seed": form_data.seed if form_data.seed is not None else request.app.state.config.AUTOMATIC1111_SEED,
        }

        # Steps
        if form_data.steps:
            data["steps"] = form_data.steps
        elif request.app.state.config.IMAGE_STEPS:
            data["steps"] = request.app.state.config.IMAGE_STEPS

        # CFG Scale
        if form_data.cfg_scale:
            data["cfg_scale"] = form_data.cfg_scale
        elif request.app.state.config.AUTOMATIC1111_CFG_SCALE:
            data["cfg_scale"] = request.app.state.config.AUTOMATIC1111_CFG_SCALE

        # Sampler
        if form_data.sampler_name:
            data["sampler_name"] = form_data.sampler_name
        elif request.app.state.config.AUTOMATIC1111_SAMPLER:
            data["sampler_name"] = request.app.state.config.AUTOMATIC1111_SAMPLER

        # Scheduler
        if form_data.scheduler:
            data["scheduler"] = form_data.scheduler
        elif request.app.state.config.AUTOMATIC1111_SCHEDULER:
            data["scheduler"] = request.app.state.config.AUTOMATIC1111_SCHEDULER

        # Hires fix
        enable_hr = form_data.enable_hr if form_data.enable_hr is not None else request.app.state.config.AUTOMATIC1111_ENABLE_HR
        if enable_hr:
            data["enable_hr"] = True
            data["hr_scale"] = form_data.hr_scale or request.app.state.config.AUTOMATIC1111_HR_SCALE
            data["hr_upscaler"] = form_data.hr_upscaler or request.app.state.config.AUTOMATIC1111_HR_UPSCALER
            data["denoising_strength"] = form_data.denoising_strength or request.app.state.config.AUTOMATIC1111_DENOISING_STRENGTH

        # Other settings
        restore_faces = form_data.restore_faces if form_data.restore_faces is not None else request.app.state.config.AUTOMATIC1111_RESTORE_FACES
        if restore_faces:
            data["restore_faces"] = True

        tiling = form_data.tiling if form_data.tiling is not None else request.app.state.config.AUTOMATIC1111_TILING
        if tiling:
            data["tiling"] = True

        # Override settings (VAE, CLIP skip)
        override_settings = {}

        clip_skip = form_data.clip_skip or request.app.state.config.AUTOMATIC1111_CLIP_SKIP
        if clip_skip:
            override_settings["CLIP_stop_at_last_layers"] = clip_skip

        vae = form_data.vae or request.app.state.config.AUTOMATIC1111_VAE
        if vae:
            override_settings["sd_vae"] = vae

        if override_settings:
            data["override_settings"] = override_settings

        # Make request to SD WebUI
        r = await asyncio.to_thread(
            requests.post,
            url=f"{request.app.state.config.AUTOMATIC1111_BASE_URL}/sdapi/v1/txt2img",
            json=data,
            headers={"authorization": get_automatic1111_api_auth(request)},
        )

        r.raise_for_status()
        res = r.json()
        log.debug(f"Advanced generation response: {res.get('info', '')[:200]}")

        images = []
        for image in res["images"]:
            image_data, content_type = load_b64_image_data(image)
            url = upload_image(
                request,
                image_data,
                content_type,
                {**data, "info": res.get("info", "")},
                user,
            )
            images.append({"url": url})

        return images

    except Exception as e:
        log.exception(f"Error in advanced image generation: {e}")
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))
