import os
import math
from itertools import chain
from pathlib import Path
import logging
import math
import re, random
import pathlib
from typing import Set

import gradio as gr
import modules.scripts as scripts

from modules.processing import process_images, fix_seed, Processed
from modules.shared import opts

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

WILDCARD_DIR = getattr(opts, "wildcard_dir", "scripts/wildcards")
MAX_RECURSIONS = 20
VERSION = "0.6.0"
WILDCARD_SUFFIX = "txt"
MAX_IMAGES = 1000

re_wildcard = re.compile(r"__(.*?)__")
re_combinations = re.compile(r"\{([^{}]*)}")

DEFAULT_NUM_COMBINATIONS = 1

class WildcardFile:
    def __init__(self, path: Path, encoding="utf8"):
        self._path = path
        self._encoding = encoding

    def get_wildcards(self) -> Set[str]:
        is_empty_line = lambda line: line is None or line.strip() == "" or line.strip().startswith("#")

        with self._path.open(encoding=self._encoding, errors="ignore") as f:
            lines = [line.strip() for line in f if not is_empty_line(line)]
            return set(lines)

class WildcardManager:
    def __init__(self, path:str=WILDCARD_DIR):
        self._path = Path(path)

    def _directory_exists(self) -> bool:
        return self._path.exists() and self._path.is_dir()

    def ensure_directory(self) -> bool:
        try:
            self._path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.exception(f"Failed to create directory {self._path}")

    def get_files(self, relative:bool=False) -> list[Path]:
        if not self._directory_exists():
            return []


        files = self._path.rglob(f"*.{WILDCARD_SUFFIX}")
        if relative:
            files = [f.relative_to(self._path) for f in files]

        return files

    def match_files(self, wildcard:str) -> list[WildcardFile]:
        return [
            WildcardFile(path) for path in self._path.rglob(f"{wildcard}.{WILDCARD_SUFFIX}")
        ]

    def get_wildcards(self) -> list[str]:
        files = self.get_files(relative=True)
        wildcards = [f"__{path.with_suffix('')}__" for path in files]
        return wildcards

wildcard_manager = WildcardManager()

class PromptGenerator:
    pass

class RandomPromptGenerator(PromptGenerator):
    def __init__(self, template):
        self._template = template

    def _replace_combinations(self, match):
        if match is None or len(match.groups()) == 0:
            logger.warning("Unexpected missing combination")
            return ""

        variants = [s.strip() for s in match.groups()[0].split("|")]
        if len(variants) > 0:
            first = variants[0].split("$$")
            quantity = DEFAULT_NUM_COMBINATIONS
            if len(first) == 2: # there is a $$
                prefix_num, first_variant = first
                variants[0] = first_variant
                
                try:
                    prefix_ints = [int(i) for i in prefix_num.split("-")]
                    if len(prefix_ints) == 1:
                        quantity = prefix_ints[0]
                    elif len(prefix_ints) == 2:
                        prefix_low = min(prefix_ints)
                        prefix_high = max(prefix_ints)
                        quantity = random.randint(prefix_low, prefix_high)
                    else:
                        raise 
                except Exception:
                    logger.warning(f"Unexpected combination formatting, expected $$ prefix to be a number or interval. Defaulting to {DEFAULT_NUM_COMBINATIONS}")
            
            try:
                picked = random.sample(variants, quantity)
                return ", ".join(picked)
            except ValueError as e:
                logger.exception(e)
                return ""

        return ""

    def _replace_wildcard(self, match):
        if match is None or len(match.groups()) == 0:
            logger.warning("Expected match to contain a filename")
            return ""

        wildcard = match.groups()[0]
        wildcard_files = wildcard_manager.match_files(wildcard)

        if len(wildcard_files) == 0:
            logging.warning(f"Could not find any wildcard files matching {wildcard}")
            return ""

        wildcards = set().union(*[f.get_wildcards() for f in wildcard_files])

        if len(wildcards) > 0:
            return random.choice(list(wildcards))
        else:
            logging.warning(f"Could not find any wildcards in {wildcard}")
            return ""
    

    def pick_variant(self, template):
        if template is None:
            return None

        return re_combinations.sub(lambda x: self._replace_combinations(x), template)

    def pick_wildcards(self, template):
        return re_wildcard.sub(lambda x: self._replace_wildcard(x), template)

    def generate_prompt(self, template):
        old_prompt = template
        counter = 0
        while True:
            counter += 1
            if counter > MAX_RECURSIONS:
                raise Exception("Too many recursions, something went wrong with generating the prompt")

            prompt = self.pick_variant(old_prompt)
            prompt = self.pick_wildcards(prompt)

            if prompt == old_prompt:
                logger.info(f"Prompt: {prompt}")
                return prompt
            old_prompt = prompt

    def generate(self, num_prompts):
        all_prompts = [
            self.generate_prompt(self._template) for _ in range(num_prompts)
        ]

        return all_prompts

class CombinatorialPromptGenerator(PromptGenerator):
    def __init__(self, template):
        self._template = template

    def generate_from_variants(self, seed_template):
        templates = [seed_template]
        new_templates = []
        variants = re_combinations.findall(templates[0])
        for variant in variants:
            for val in variant.split("|"):
                for template in templates:
                    new_templates.append(template.replace(f"{{{variant}}}", val, 1))
            templates = new_templates
            new_templates = []

        if len(templates) == 0:
            return [seed_template]
        return templates

    def generate_from_wildcards(self, seed_template):
        templates = [seed_template]
        all_prompts = []
        count = 0

        while True:
            count += 1
            if count > MAX_RECURSIONS:
                raise Exception("Too many recursions, something went wrong with generating the prompt")

            if len(templates) == 0:
                break

            template = templates.pop(0)
            wildcards = re_wildcard.findall(template)
            if len(wildcards) == 0:
                all_prompts.append(template)
                continue

            for wildcard in wildcards:
                wildcard_files = wildcard_manager.match_files(wildcard)
                for val in chain(*[f.get_wildcards() for f in wildcard_files]):
                    templates.append(template.replace(f"__{wildcard}__", val, 1))
        return all_prompts

    def generate(self, max_prompts=MAX_IMAGES):
        templates = [self._template]
        all_prompts = []

        while True:
            if len(templates) == 0 or len(all_prompts) > max_prompts:
                break

            template = templates.pop(0)
            new_prompts = self.generate_from_wildcards(template)
            templates.extend(new_prompts)

            template = templates.pop(0)
            new_prompts = self.generate_from_variants(template)
            no_new_prompts = len(new_prompts) == 1

            if no_new_prompts:
                all_prompts.append(new_prompts[0])
            else:
                templates.extend(new_prompts)

        return all_prompts[:max_prompts]

class Script(scripts.Script):
    def title(self):
        return f"Dynamic Prompting v{VERSION}"

    def ui(self, is_img2img):
        html = f"""
            <h3><strong>Combinations</strong></h3>
            Choose a number of terms from a list, in this case we choose two artists
            <code>{{2$$artist1|artist2|artist3}}</code>
            If $$ is not provided, then 1$$ is assumed.
            <br>
            A range can be provided:
            <code>{{1-3$$artist1|artist2|artist3}}</code>
            In this case, a random number of artists between 1 and 3 is chosen.
            <br/><br/>

            <h3><strong>Wildcards</strong></h3>
            <p>Available wildcards</p>
            <ul style="overflow-y:auto;max-height:6rem;">
        """
        
        wildcards = wildcard_manager.get_wildcards()
        html += "".join([f"<li>{wildcard}</li>" for wildcard in wildcards])

        html += "</ul>"
        html += f"""
            <br/>
            <code>WILDCARD_DIR: {WILDCARD_DIR}</code><br/>
            <small>You can add more wildcards by creating a text file with one term per line and name is mywildcards.txt. Place it in {WILDCARD_DIR}. <code>__mywildcards__</code> will then become available.</small>
        """
        is_exhaustive = gr.Checkbox(label="Combinatorial generation", title="This is some help text", value=False)
        info = gr.HTML(html)
        return [info, is_exhaustive]

    def exhaustive_generation(self, prompt):
        pass

    def run(self, p, info, is_exhaustive):
        fix_seed(p)

        original_prompt = p.prompt[0] if type(p.prompt) == list else p.prompt
        original_seed = p.seed

        if not is_exhaustive:
            prompt_generator = RandomPromptGenerator(original_prompt)
        else:
            prompt_generator = CombinatorialPromptGenerator(original_prompt)
        
        num_images = p.n_iter * p.batch_size
        all_prompts = prompt_generator.generate(num_images)

        all_seeds = [int(p.seed) + (x if p.subseed_strength == 0 else 0) for x in range(num_images)]

        logger.info(f"Prompt matrix will create {len(all_prompts)} images in a total of {p.n_iter} batches.")

        p.prompt = all_prompts
        p.seed = all_seeds

        p.prompt_for_display = original_prompt
        processed = process_images(p)

        p.prompt = original_prompt
        p.seed = original_seed

        return processed

wildcard_manager.ensure_directory()
