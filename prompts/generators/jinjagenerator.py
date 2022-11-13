from jinja2 import Environment
from jinja2.ext import Extension
import jinja2.nodes
import random
from jinja2.exceptions import TemplateSyntaxError
from pathlib import Path
from prompts.generators import re_wildcard, re_combinations
from prompts.generators.promptgenerator import GeneratorException
import logging

logger = logging.getLogger(__name__)

class ChoiceExtension(Extension):
    def __init__(self, environment):
        super(ChoiceExtension, self).__init__(environment)
        environment.globals['choice'] = self.choice

    def choice(self, *items):
        return random.choice(items)

class WildcardExtension(Extension):
    def __init__(self, environment):
        super(WildcardExtension, self).__init__(environment)
        environment.globals['wildcard'] = self.wildcard

    def wildcard(self, wildcard_name):
        wm = self.environment.wildcard_manager
        values = []

        for value in wm.get_all_values(wildcard_name):
            if re_wildcard.fullmatch(value):
                values.extend(self.wildcard(value))
            elif re_combinations.fullmatch(value):
                val = re_combinations.findall(value)[0]
                options = val.split('|')
                choice_ext = ChoiceExtension(self.environment)
                values.append(choice_ext.choice(options))
            else:
                values.append(value)
        return values

class PromptExtension(Extension):
    tags = {"prompt"}

    def __init__(self, environment):
        super(PromptExtension, self).__init__(environment)
        environment.extend(prompt_blocks=[])


    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(['name:endprompt'], drop_needle=True)
        return jinja2.nodes.CallBlock(self.call_method('_prompt', []), [], [], body).set_lineno(lineno)

    def _prompt(self, caller):
        self.environment.prompt_blocks.append(caller())
        return caller()

from .promptgenerator import PromptGenerator

class JinjaGenerator(PromptGenerator):
    def __init__(self, template, wildcard_manager=None):
        self._template = template
        self._wildcard_manager = wildcard_manager

    def generate(self, num_prompts=1):
        try:
            env = Environment(extensions=[ChoiceExtension, PromptExtension, WildcardExtension])
            env.wildcard_manager = self._wildcard_manager

            prompts = []
            for i in range(num_prompts):
                template = env.from_string(self._template)
                s = template.render()
                prompts.append(s)

            if env.prompt_blocks:
                prompts = env.prompt_blocks
            return prompts
        except TemplateSyntaxError as e:
            logger.exception(e)
            raise GeneratorException(e.message)