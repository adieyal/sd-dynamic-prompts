from itertools import chain
from pathlib import Path
from typing import Any
from typing import Set
import logging
import math
import os
import pathlib
import re, random

import gradio as gr

import modules.scripts as scripts
from modules.processing import process_images, fix_seed, Processed
from modules.shared import opts

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

WILDCARD_DIR = getattr(opts, "wildcard_dir", "scripts/wildcards")
MAX_RECURSIONS = 20
VERSION = "0.9.0"
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
    
    def path_to_wilcard(self, path: Path) -> str:
        rel_path = path.relative_to(self._path)
        return f"__{rel_path.with_suffix('')}__"

    def get_wildcards(self) -> list[str]:
        files = self.get_files(relative=True)
        wildcards = [self.path_to_wilcard(f) for f in files]

        return wildcards

    def get_wildcard_hierarchy(self, path: str):
        path = Path(path)
        files = path.glob("*.txt")
        wildcards = [self.path_to_wilcard(f) for f in files]
        directories = [d for d in path.glob("*") if d.is_dir()]

        hierarchy = {d.name: self.get_wildcard_hierarchy(d) for d in directories}
        return (wildcards, hierarchy)

wildcard_manager = WildcardManager()

class UiCreation:
    def write(self, wildcards: list[str], hierarchy: dict[str, Any]) -> str:
        html = ""
        for wildcard in wildcards:
            html += f"<p>{wildcard}</p>"

        for directory, h in hierarchy.items():
            contents = self.write(h[0], h[1])
            html += f"""
                <button type="button" class="collapsible">{directory} :</button>
                <div class="content">
                    {contents}
                </div>
            """

        return html

    def probe(self) -> str:
        wildcards, hierarchy = wildcard_manager.get_wildcard_hierarchy(WILDCARD_DIR)
        return self.write(wildcards, hierarchy)


ui_creation = UiCreation()

def replace_combinations(match):
    if match is None or len(match.groups()) == 0:
        logger.warning("Unexpected missing combination")
        return ""

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

    def generate_from_wildcards(self, seed_template, recursion=0):
        templates = []

        if recursion > MAX_RECURSIONS:
            raise Exception("Too many recursions, something went wrong with generating the prompt: " + seed_template)

        template = seed_template
        wildcards = re_wildcard.findall(template)
        if len(wildcards) == 0:
            return [template]

        for wildcard in wildcards:
            wildcard_files = wildcard_manager.match_files(wildcard)
            for val in chain(*[f.get_wildcards() for f in wildcard_files]):
                new_template = template.replace(f"__{wildcard}__", val, 1)
                logging.debug(f"New template: {new_template}")
                templates.append(new_template)

        new_templates = []
        for template in templates:
            new_templates += self.generate_from_wildcards(template, recursion=recursion + 1)

        return new_templates


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
        wildcard_html = ui_creation.probe()
        html = f"""
            <style>
                .collapsible {{
                    background-color: #1f2937;
                    color: white;
                    cursor: pointer;
                    padding: 18px;
                    width: 100%;
                    border: 2px #0C111C;
                    border-right-style: solid;
                    border-top-style: solid;
                    border-left-style: solid;
                    border-bottom-style: solid;
                    border-radius: 8px 8px 8px 8px;
                    padding: 5px;
                    margin-top: 10px;
                    text-align: left;
                    outline: none;
                    font-size: 15px;
                }}

                .active, .collapsible:hover {{
                    background-color: #555;
                }}

                .codeblock {{
                    background-color: #06080D;
                }}

                .content {{
                    padding: 0 18px;
                    display: none;
                    overflow: hidden;
                    border: 2px #0C111C;
                    border-right-style: solid;
                    border-bottom-style: solid;
                    border-left-style: solid;
                    border-radius: 0px 0px 8px 8px;
                    background-color: #1f2937;
                }}

                #is-combinatorial:after {{
                    content: "Generate all possible prompts up to a maximum of Batch count * Batch size)"
                }}
            </style>


            <h3><strong>Combinations</strong></h3>
            Choose a number of terms from a list, in this case we choose two artists: 
            <code class="codeblock">{{2$$artist1|artist2|artist3}}</code>

            If $$ is not provided, then 1$$ is assumed.

            A range can be provided:
            <code class="codeblock">{{1-3$$artist1|artist2|artist3}}</code>
            In this case, a random number of artists between 1 and 3 is chosen.

            <br/><br/>

            <h3><strong>Wildcards</strong></h3>
            {wildcard_html}

			<br/>
            If the groups wont drop down click <strong onclick="check_collapsibles()" style="cursor: pointer">here</strong> to fix the issue.

            <br/><br/>

            <code class="codeblock">WILDCARD_DIR: {WILDCARD_DIR}</code><br/>
            <small onload="check_collapsibles()">You can add more wildcards by creating a text file with one term per line and name is mywildcards.txt. Place it in {WILDCARD_DIR}. <code class="codeblock">__&#60;folder&#62;/mywildcards__</code> will then become available.</small>
        """
        is_combinatorial = gr.Checkbox(label="Combinatorial generation", title="This is some help text", value=False, elem_id="is-combinatorial")
        info = gr.HTML(html)
        return [info, is_combinatorial]

    def run(self, p, info, is_combinatorial):
        fix_seed(p)

        original_prompt = p.prompt[0] if type(p.prompt) == list else p.prompt
        original_seed = p.seed

        if is_combinatorial:
            prompt_generator = CombinatorialPromptGenerator(original_prompt)
        else:
            prompt_generator = RandomPromptGenerator(original_prompt)
        
        num_images = p.n_iter * p.batch_size
        all_prompts = prompt_generator.generate(num_images)
        updated_count = len(all_prompts)
        p.n_iter = math.ceil(updated_count / p.batch_size)

        all_seeds = [int(p.seed) + (x if p.subseed_strength == 0 else 0) for x in range(updated_count)]

        logger.info(f"Prompt matrix will create {updated_count} images in a total of {p.n_iter} batches.")

        p.prompt = all_prompts
        p.seed = all_seeds

        p.prompt_for_display = original_prompt
        processed = process_images(p)

        p.prompt = original_prompt
        p.seed = original_seed

        return processed

wildcard_manager.ensure_directory()
