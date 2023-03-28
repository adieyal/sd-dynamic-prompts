from dynamicprompts.generators import RandomPromptGenerator

from sd_dynamic_prompts.frozenprompt_generator import FrozenPromptGenerator


def test_repeats_correctly():
    generator = FrozenPromptGenerator(RandomPromptGenerator())
    template = "{A|B|C|D|E|F|G|H|I|J|K}"
    prompts = generator.generate(template, 10)

    assert len(prompts) == 10
    assert len(set(prompts)) == 1

    prompts2 = generator.generate(template, 10)

    assert len(prompts2) == 10
    assert len(set(prompts2)) == 1

    assert prompts[0] != prompts2[0]
