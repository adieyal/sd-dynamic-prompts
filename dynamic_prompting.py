import os
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

    def get_files(self, relative:bool=False) -> list():
        if not self._directory_exists():
            return []

        files = self._path.rglob(f"*.{WILDCARD_SUFFIX}")
        if relative:
            files = [f.relative_to(self._path) for f in files]

        return files

    def match_files(self, wildcard:str) -> list():
        return [
            WildcardFile(path) for path in self._path.rglob(f"{wildcard}.{WILDCARD_SUFFIX}")
        ]

    def get_wildcards(self) -> list():
        files = self.get_files(relative=True)
        wildcards = [f"__{path.with_suffix('')}__" for path in files]
        return wildcards

class UiCreation:
    def write(self, path):
        if path.is_dir():
            return self.write_dir(path)
        else:
            return self.write_txt(path)        

    def write_txt(self, path):
        temp = ""
        filename = path.name
        wildcard = "__" + "/".join((str(path).split("\\"))[2:-1])+ "/" + filename.replace(".txt", "") + "__"

        temp += f"<p>{wildcard}</p>"
        return temp

    def write_dir(self, path):
        temp = ""
        Ppath = "/".join(str(path).split("\\")[2:])
        temp += f"<button type=\"button\" class=\"collapsible\">{Ppath} :</button>"
        temp += f"<div class=\"content\">"
        
        for file_or_dir in list(pathlib.Path(path).glob('*/')):
            temp += self.write(file_or_dir)

        temp += f"</div>"
        return temp 

    def probe(self, dir):
        temp = ""
        directories = list(pathlib.Path(dir).glob('*/')) #.rglob("*txt")
        for dirs in directories[0:]:
            temp += self.write(dirs)
        return temp

ui_creation = UiCreation()
wildcard_manager = WildcardManager()

def replace_combinations(match):
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

def replace_wildcard(match):
    is_empty_line = lambda line: line is None or line.strip() == "" or line.strip().startswith("#")
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
    
def pick_wildcards(template):
    return re_wildcard.sub(replace_wildcard, template)


def pick_variant(template):
    if template is None:
        return None

    return re_combinations.sub(replace_combinations, template)

def generate_prompt(template):
    old_prompt = template
    counter = 0
    while True:
        counter += 1
        if counter > MAX_RECURSIONS:
            raise Exception("Too many recursions, something went wrong with generating the prompt")

        prompt = pick_variant(old_prompt)
        prompt = pick_wildcards(prompt)

        if prompt == old_prompt:
            logger.info(f"Prompt: {prompt}")
            return prompt
        old_prompt = prompt
        
class Script(scripts.Script):
    def title(self):
        return f"Dynamic Prompting v{VERSION}"

    def ui(self, is_img2img):
        html = """
            <style>
            .collapsible {
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
            }

            .active, .collapsible:hover {
            background-color: #555;
            }

            .codeblock {
                background-color: #06080D;
            }

            .content {
            padding: 0 18px;
            display: none;
            overflow: hidden;
            border: 2px #0C111C;
            border-right-style: solid;
            border-bottom-style: solid;
            border-left-style: solid;
            border-radius: 0px 0px 8px 8px;
            background-color: #1f2937;
            }
            </style>
        """

        html += f"""
            If the groups wont drop down click <strong onclick="check_collapsibles()" style="cursor: pointer">here</strong> to fix the issue.
            <br/><br/>
            <h3><strong>Combinations</strong></h3>
            Choose a number of terms from a list, in this case we choose two artists: 
            <code class="codeblock">{{2$$artist1|artist2|artist3}}</code>
            If $$ is not provided, then 1$$ is assumed.
            A range can be provided:
            <code class="codeblock">{{1-3$$artist1|artist2|artist3}}</code>
            In this case, a random number of artists between 1 and 3 is chosen.
            <br/><br/>
            <h3><strong>Wildcards</strong></h3>
        """
        
        #wildcards = wildcard_manager.get_wildcards()
        html += ui_creation.probe(WILDCARD_DIR) #"".join([f"<li>{wildcard}</li>" for wildcard in wildcards])

        html += f"""
            <br/><br/>
            <code class="codeblock">WILDCARD_DIR: {WILDCARD_DIR}</code><br/>
            <small onload="check_collapsibles()">You can add more wildcards by creating a text file with one term per line and name is mywildcards.txt. Place it in {WILDCARD_DIR}. <code class="codeblock">__&#60;folder&#62;/mywildcards__</code> will then become available.</small>
        """
        info = gr.HTML(html)
        return [info]

    def run(self, p, info):
        fix_seed(p)

        original_prompt = p.prompt[0] if type(p.prompt) == list else p.prompt
        original_seed = p.seed
        
        num_images = p.n_iter * p.batch_size
        all_prompts = [
            generate_prompt(original_prompt) for _ in range(num_images)
        ]

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
