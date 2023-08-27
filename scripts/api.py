import gradio as gr
import logging
from fastapi import FastAPI, Body

from modules.processing import StableDiffusionProcessing
from sd_dynamic_prompts.dynamic_prompting import Script

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def controlnet_api(_: gr.Blocks, app: FastAPI):
    @app.post("/dynamicprompts/evaluate")
    async def evaluate(
            prompt: str = Body("", title="Prompt"),
            negative_prompt: str = Body("", title="Negative Prompt"),
            is_combinatorial: bool = Body(False, title="Is combinatorial"),
            combinatorial_batches: int = Body(1, title="Combinatorial batches"),
            batch_size: int = Body(1, title="Batch size"),
            max_generations: int = Body(0, title="Max generations"),
            seed: int = Body(1, title="Seed"),
    ):
        script = Script()

        all_prompts, all_negative_prompts = script.generate_prompts(
            p=StableDiffusionProcessing(),
            original_prompt=prompt,
            original_negative_prompt=negative_prompt,
            original_seed=seed,
            num_images=batch_size,
            is_combinatorial=is_combinatorial,
            combinatorial_batches=combinatorial_batches,
            max_generations=max_generations,
        )
        return {
            "all_prompts": all_prompts,
            "all_negative_prompts": all_negative_prompts,
        }


try:
    import modules.script_callbacks as script_callbacks

    script_callbacks.on_app_started(controlnet_api)
except:
    pass
