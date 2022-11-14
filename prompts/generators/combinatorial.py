from __future__ import annotations
from itertools import chain
import logging

from prompts.wildcardmanager import WildcardManager
from prompts import constants
from . import PromptGenerator, re_combinations, re_wildcard

logger = logging.getLogger(__name__)


class CombinatorialPromptGenerator(PromptGenerator):
    def __init__(self, wildcardmanager: WildcardManager, template):
        self._wildcard_manager = wildcardmanager
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

    def generate_from_wildcards(self, seed_template, max_prompts, recursion=0) -> list[str]:
        templates = []

        if recursion > constants.MAX_RECURSIONS:
            raise Exception("Too many recursions, something went wrong with generating the prompt: " + seed_template)

        template = seed_template
        wildcards = re_wildcard.findall(template)
        if len(wildcards) == 0:
            return [template]

        for wildcard in wildcards:
            wildcard_files = self._wildcard_manager.match_files(wildcard)
            for val in chain(*[f.get_wildcards() for f in wildcard_files]):
                new_template = template.replace(f"__{wildcard}__", val, 1)
                logger.debug(f"New template: {new_template}")
                
                if len(templates) >= max_prompts:
                    break
                templates.append(new_template)
                

        new_templates = []
        for template in templates:
            new_templates += self.generate_from_wildcards(template, max_prompts, recursion=recursion + 1)

        return list(set(new_templates))


    def generate(self, max_prompts=constants.MAX_IMAGES) -> list[str]:
        templates = [self._template]
        all_prompts = []

        while True:
            all_prompts = list(set(all_prompts))
            if len(templates) == 0 or len(all_prompts) > max_prompts:
                break

            template = templates.pop(0)
            new_prompts = self.generate_from_wildcards(template, max_prompts)
            templates.extend(new_prompts)

            if len(templates) == 0:
                break

            template = templates.pop(0)
            new_prompts = self.generate_from_variants(template)
            no_new_prompts = len(new_prompts) == 1

            if no_new_prompts:
                all_prompts.append(new_prompts[0])
            else:
                templates.extend(new_prompts)

        if len(all_prompts) == 0:
            logger.warning(f"No prompts generated for template: {self._template}")
            return [self._template]
        return all_prompts[:max_prompts]


