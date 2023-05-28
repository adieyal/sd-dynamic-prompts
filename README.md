# Stable Diffusion Dynamic Prompts extension
A custom extension for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) that implements an expressive template language for random or combinatorial prompt generation along with features to support deep wildcard directory structures.

<p align="center">
    <a href="docs/SYNTAX.md"><img src="images/icon-syntax.png" valign="middle" style="height:60px;margin-right:10px"/></a>
    <a href="docs/tutorial.md"><img src="images/icon-tutorial.png" valign="middle" style="height:60px;margin-right:10px"/></a>
    <a href="docs/CHANGELOG.md"><img src="images/icon-changelog.png" valign="middle" style="height:60px"/></a>
</p>

<img src="images/extension.png"/>

## Table of Contents

   * [Basic Usage](#basic-usage)
   * [Online resources](#online-resources)
   * [Installation](#installation)
   * [Configuration](#configuration)
   * [Troubleshooting](#troubleshooting)
   * [Compatible Scripts](#compatible-scripts)
   * [Template syntax](#template-syntax)
      * [Fuzzy Glob/recursive wildcard file/directory matching](#fuzzy-globrecursive-wildcard-filedirectory-matching)
   * [Combinatorial Generation](#combinatorial-generation)
      * [Combinatorial Batches](#combinatorial-batches)
      * [Increasing the maximum number of generations](#increasing-the-maximum-number-of-generations)
   * [Fixed seed](#fixed-seed)
   * [Magic Prompt](#magic-prompt)
      * [Other models](#other-models)
   * [I'm feeling lucky](#im-feeling-lucky)
   * [Attention grabber](#attention-grabber)
   * [Write prompts to file](#write-prompts-to-file)
   * [Jinja2 templates](#jinja2-templates)
   * [WILDCARD_DIR](#wildcard_dir)
   * [Collections](#collections)
   * [Dynamic Prompts and Random Seeds](#dynamic-prompts-and-random-seeds)
      * [Without Dynamic Prompts Enabled](#without-dynamic-prompts-enabled)
      * [With Dynamic Prompts Enabled in Random/Standard Mode](#with-dynamic-prompts-enabled-in-randomstandard-mode)
      * [Variation Seeds with Dynamic Prompts](#variation-seeds-with-dynamic-prompts)
      * [Combinatorial Mode with Variation Strength &gt; 0](#combinatorial-mode-with-variation-strength--0)


## Basic Usage
Using this script, the prompt:

	A {house|apartment|lodge|cottage} in {summer|winter|autumn|spring} by {2$$artist1|artist2|artist3}

Will produce any of the following prompts:

- A **house** in **summer** by **artist1**, **artist2**
- A **lodge** in **autumn** by **artist3**, **artist1**
- A **cottage** in **winter** by **artist2**, **artist3**
- ...

This is especially useful if you are searching for interesting combinations of artists and styles.

You can also pick a random string from a file. Assuming you have the file seasons.txt in WILDCARD_DIR (see below), then:

    __seasons__ is coming

Might generate the following:

- Winter is coming
- Spring is coming
- ...

You can also use the same wildcard twice

    I love __seasons__ better than __seasons__

- I love Winter better than Summer
- I love Spring better than Spring

More complete documentation can be found [here](docs/SYNTAX.md).<br/>
Prefer a tutorial? <a href="docs/tutorial.md">Click here</a><br/>
Need a wildcard library? We've got you [covered](https://github.com/adieyal/sd-dynamic-prompts#collections).<br/>

## Online resources
* 📽️ [아무것도 생각 안 하고 그림 뽑는 방법 (stable diffusion Dynamic Prompts extension)](https://www.youtube.com/watch?v=P6Tl5sMUJpk)
* 📽️ [Dynamic Prompt Tutorial: How to Create Multiple Art Variations with just 1 Prompt Stable Diffusion](https://www.youtube.com/watch?v=5wH7zioje4w)
* 📽️ [Experiment with Prompts FAST in Stable Diffusion](https://www.youtube.com/watch?v=5ZiL4iG0FJk)
* [Having a blast with ControlNet + Dynamic Prompts (Wildcards)](https://www.reddit.com/r/StableDiffusion/comments/115t0pi/having_a_blast_with_controlnet_dynamic_prompts/)
* [Infinite Random RPG Character Portraits with Dynamic Prompts](https://www.reddit.com/r/StableDiffusion/comments/10xqwjm/i_come_bearing_gifts_infinite_random_rpg/)
* [256 unique characters created with dynamic prompts ](https://www.reddit.com/r/StableDiffusion/comments/106hxm1/256_unique_characters_created_with_dynamic/)
* [Use ChatGPT to create powerful and useful wildcards with the Dynamic Prompts extension](https://www.reddit.com/r/StableDiffusion/comments/10m6b4a/use_chatgpt_to_create_powerful_and_useful/)
* [200 Character/outfit designs from a single prompt using Dynamic Prompts and Prompt Editing](https://www.reddit.com/r/StableDiffusion/comments/1080xyy/200_characteroutfit_designs_from_a_single_prompt/)
* [Dynamic Prompts and Jinja2 templates in Automatic 1111](https://www.reddit.com/r/StableDiffusion/comments/10jgmtk/dynamic_prompts_and_jinja2_templates_in_automatic/)
* [Testing Dynamic Prompts extension to mix and match elements](https://www.reddit.com/r/StableDiffusion/comments/10gkm1c/testing_dynamic_prompts_extension_to_mix_and/)
* [How to Turbocharge your prompts using AUTOMATIC1111 WebUI dynamic prompts extension](https://www.reddit.com/r/StableDiffusion/comments/ynztiz/how_to_turbocharge_your_prompts_using/)
* [Dynamic prompts for Automatic1111 is so incredibly powerful, these are all from the same prompt!](https://www.reddit.com/r/StableDiffusion/comments/zacjhk/dynamic_prompts_for_automatic1111_is_so/)

## Installation

The extension can be installed directly from within the **Extensions** tab within the Webui
<img src="images/installation.png"/>

You can also install it manually by running the following command from within the webui directory:

	git clone https://github.com/adieyal/sd-dynamic-prompting/ extensions/dynamic-prompts

## Configuration
In case of a syntax clash with another extension, Dynamic Prompts allows you to change the definition of variant start and variant end. By default these are set to `{` and `}` respectively. , e.g. `{red|green|blue}`. In the settings tab, you can change these two any string, e.g. `<red|green|blue>` or even `::red|green|blue::`.

<img src="images/config_brackets.png">

By default, wildcards start with `__`(double underscore) and end with `__`. You can change this in the settings tab under wildcard wrap.

## Troubleshooting
If you encounter an issue with Dynamic Prompts, follow these steps to resolve the problem:

1. Check that you have installed the latest version of both the Dynamic Prompts extension and library. To check the installed versions, open the **Need Help? accordion** in the Dynamic Prompts section of txt2image. You can find the latest version number of the extension [here](https://github.com/adieyal/sd-dynamic-prompts/blob/main/docs/CHANGELOG.md) and the library [here](https://github.com/adieyal/dynamicprompts/blob/main/CHANGELOG.md?plain=1).

2. If the versions do not match, update the extension in the extensions tab and restart the webui. The extension should automatically update the library.

3. If the above step does not work, you might need to manually update the library using the following command:

```shell
python -m pip install -U dynamicprompts[attentiongrabber,magicprompt]
```

4. Restart the webui and check. If the webui uses a different python binary, find the correct path to the python binary and run:

```shell
/path/to/python/binary/python -m pip install -U dynamicprompts[attentiongrabber,magicprompt]
```

5. If the Wildcard UI does not show, it could be due to an outdated library version. Check for errors in the terminal and update the library as described in step 3.

6. If you get an error message saying "No values found for wildcard some/wildcard", ensure that the file wildcard.txt is in extensions/sd-dynamic-prompts/wildcards/some/. The full path is required, as relative paths are not currently supported.

7. If the issue persists, search for solutions in the [issues section](https://github.com/adieyal/sd-dynamic-prompts/issues?q=is%3Aissue) on Github and the [discussion forum](https://github.com/adieyal/sd-dynamic-prompts/discussions). If you cannot find a solution, create a new issue and give it a descriptive name, such as "Wildcard values are being ignored in prompt templates". Provide the necessary context, including the versions of the Dynamic Prompts extension and library, and mention the operating system or colab being used. If there is an error in the terminal, copy and paste the entire text or take a screenshot.

8. Finally, it is essential to test and apply any fixes we release. Your feedback is valuable, as an issue that works in our environment may not work in yours.

## Compatible Scripts
Dynamic Prompts works particularly well with X/Y Plot - setting Dynamic Prompts to <a href="#combinatorial-generation">combinatorial mode</a> while using X/Y Plot, lets you exhaustively test prompt and paramter variations simultaneously.


## Template syntax
Documentation can be found [here](docs/SYNTAX.md)

### Fuzzy Glob/recursive wildcard file/directory matching
In addition to standard wildcard tokens such as `__times__` -> `times.txt`, you can also use globbing to match against multiple files at once.
For instance:

`__colors*__` will match any of the following:
- WILDCARD_DIR/colors.txt
- WILDCARD_DIR/colors1.txt
- WILDCARD_DIR/nested/folder/colors1.txt

`__light/**/*__` will match:
- WILDCARD_DIR/nested/folder/light/a.txt
- WILDCARD_DIR/nested/folder/light/b.txt

but won't match
- WILDCARD_DIR/nested/folder/dark/a.txt
- WILDCARD_DIR/a.txt

You can also used character ranges `[0-9]` and `[a-z]` and single wildcard characters `?`. For more examples see [this article](http://pymotw.com/2/glob/).

## Combinatorial Generation
Instead of generating random prompts from a template, combinatorial generation produced every possible prompt from the given string. For example:
`I {love|hate} {New York|Chicago} in {June|July|August}`

will produce:
- I love New York in June
- I love New York in July
- I love New York in August
- I love Chicago in June
- I love Chicago in July
- I love Chicago in August
- I hate New York in June
- I hate New York in July
- I hate New York in August
- I hate Chicago in June
- I hate Chicago in July
- I hate Chicago in August

If a `__wildcard__` is provided, then a new prompt will be produced for every value in the wildcard file. For example:
`My favourite season is __seasons__`

will produce:
- My favourite season is Summer
- My favourite season is August
- My favourite season is Winter
- My favourite season is Sprint

<img src="images/combinatorial_generation.png"/>

You also arbitrarily nest combinations inside wildcards and wildcards in combinations.

Combinatorial generation can be useful if you want to create an image for every artist in a file. It can be enabled by checking the __Combinatorial generation__ checkbox in the ui. In order to prevent accidentially producing thousands of images, you can limit the total number of prompts generated using the **Max Generations** slider. A value of 0 (the default) will not set any limit.

### Combinatorial Batches
The combinatorial batches slider lets you repeat the same set of prompts a number of times with different seeds. The default number of batches is 1.

### Increasing the maximum number of generations
By default, the __Batch count__ silder of  automatic1111 has a maximum value of 100. This can limit the maximum number of generations when using combinatorial generation. You can change the maximum value of this slider by editing ui-config.json and change:

	txt2img/Batch count/maximum": 100

to something larger like:

	txt2img/Batch count/maximum": 1000

## Fixed seed
Select this if you want to use the same seed for every generated image. If there are no wildcards then all the images will be identical. It is useful if you want to test the effect of a particular modifier. For example:

	A beautiful day at the beach __medium/photography/filmtypes__

That way you can isolate the effect of each film type on a particular scene. Here are some of the results:
<img src="images/filmtypes.jpg"/>

## Magic Prompt
Use one of a number of prompt generation models to spice up your prompt.

Using [Gustavosta](https://huggingface.co/Gustavosta/MagicPrompt-Stable-Diffusion)'s MagicPrompt model, Trained on 80,000 prompts from [Lexica.art](lexica.art), it can help give you interesting new prompts on a given subject. Here are some automatically generated variations for "dogs playing football":

> dogs playing football, in the streets of a japanese town at night, with people watching in wonder, in the style of studio ghibli and makoto shinkai, highly detailed digital art, trending on artstation

> dogs playing football, in the background is a nuclear explosion. photorealism. hq. hyper. realistic. 4 k. award winning.

> dogs playing football, in the background is a nuclear explosion. photorealistic. realism. 4 k wideshot. cinematic. unreal engine. artgerm. marc simonetti. jc leyendecker

This is compatible with the wildcard syntax described above.

### Other models
* [daspartho/prompt-extend (~500mb)](https://huggingface.co/daspartho/prompt-extend)
* [succinctly/text2image-prompt-generator (~600mb)](https://huggingface.co/succinctly/text2image-prompt-generator) - Trained on Midjourney prompts
* [microsoft/Promptist (~500mb)](https://huggingface.co/microsoft/Promptist) - Read the paper [here](https://arxiv.org/abs/2212.09611)
* [AUTOMATIC/promptgen-lexart (~300mb)](https://huggingface.co/AUTOMATIC/promptgen-lexart) - Finetuned using 134,819 prompts from lexica.art
* [AUTOMATIC/promptgen-majinai-safe (~300mb)](https://huggingface.co/AUTOMATIC/promptgen-majinai-safe) - 1,654 prompts from majinai.art
* [AUTOMATIC/promptgen-majinai-unsafe (~300mb)](https://huggingface.co/AUTOMATIC/promptgen-majinai-unsafe) - 825 prompts from majinai.art (NSFW)
* [Gustavosta/MagicPrompt-Dalle](https://huggingface.co/Gustavosta/MagicPrompt-Dalle)
* [kmewhort/stable-diffusion-prompt-bolster (~500mb)](https://huggingface.co/kmewhort/stable-diffusion-prompt-bolster),
* [Ar4ikov/gpt2-650k-stable-diffusion-prompt-generator (~500mb)](Ar4ikov/gpt2-650k-stable-diffusion-prompt-generator),
* [Ar4ikov/gpt2-medium-650k-stable-diffusion-prompt-generator (~1.4gb)](https://huggingface.co/Ar4ikov/gpt2-medium-650k-stable-diffusion-prompt-generator),
* [crumb/bloom-560m-RLHF-SD2-prompter-aesthetic (~1.1gb)](https://huggingface.co/crumb/bloom-560m-RLHF-SD2-prompter-aesthetic),
* [Meli/GPT2-Prompt (~500mb)](https://huggingface.co/Meli/GPT2-Prompt),
* [DrishtiSharma/StableDiffusion-Prompt-Generator-GPT-Neo-125M (~550mb)](https://huggingface.co/DrishtiSharma/StableDiffusion-Prompt-Generator-GPT-Neo-125M)

The first time you use a model, it is downloaded. It is approximately 500mb and so will take some time depending on how fast your connection is. It will also take a few seconds on first activation as the model is loaded into memory. Note, if you're low in VRAM, you might get a Cuda error. My GPU uses less than 8GB but YMMV.

<img src="images/magic_prompt.png"/>


You can control the maximum prompt length with the __Max magic prompt length__ slider. __Magic prompt creativity__ can adjust the generated prompt but you will need to experiment with this setting.

Use the __Magic prompt blocklist regex__ to filter out keywords. For example, if you want to avoid prompts containing Greg Rutkowski, add his name to this field.

If you are generating many prompts using Magic Prompt, then increasing the __Magic Prompt batch size__ can improve significantly improve prompt generation speed. This may only be noticeable if you are not generating images as well since image generation is much slower than prompt generation.


## I'm feeling lucky
Use the [lexica.art](https://lexica.art) API to create random prompts. Useful if you're looking for inspiration, or are simply too lazy to think of your own prompts. When this option is selected, the prompt in the main prompt box is used as a search string. For example, prompt "Mech warrior" might return:

* A large robot stone statue in the middle of a forest by Greg Rutkowski, Sung Choi, Mitchell Mohrhauser, Maciej Kuciara, Johnson Ting, Maxim Verehin, Peter Konig, final fantasy , 8k photorealistic, cinematic lighting, HD, high details, atmospheric,
* a beautiful portrait painting of a ( ( ( cyberpunk ) ) ) armor by simon stalenhag and pascal blanche and alphonse mucha and nekro. in style of digital art. colorful comic, film noirs, symmetry, brush stroke, vibrating colors, hyper detailed. octane render. trending on artstation
* symmetry!! portrait of a robot astronaut, floral! horizon zero dawn machine, intricate, elegant, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration, art by artgerm and greg rutkowski and alphonse mucha, 8 k

<img src="images/feeling-lucky.png">

Leaving the prompt box blank returns a list of completely randomly chosen prompts.

## Attention grabber
This option randomly selects a keyword in your prompt and adds a random amount of emphasis. Below is an example of how this affects the prompt:

	a portrait an anthropomorphic panda mage casting a spell, wearing mage robes, landscape in background, cute, dnd character art portrait, by jason felix and peter mohrbacher, cinematic lighting

<img src="images/emphasis.png">

Tick the __Fixed seed__ checkbox under __Advanced options__ to see how emphasis changes your image without changing seed.


## Write prompts to file
Check the write prompts to file checkbox in order to create a file with all generated prompts. The generated file is a slugified version of the prompt and can be found in the same directory as the generated images, e.g. outputs/txt2img-images
<img src="images/write_prompts.png"/>

## Jinja2 templates
[Jinja2 templates](https://jinja.palletsprojects.com/en/3.1.x/templates/) is an experimental feature that enables you to define prompts imperatively. This is an advanced feature and is only recommended for users who are comfortable writing scripts.

To enable, open the advanced accordion and select __Enable Jinja2 templates__.
<img src="images/jinja_templates.png">

You can read about them in more detail <a href="jinja2.md">here</a>

## WILDCARD_DIR
The extension looks for wildcard files in WILDCARD_DIR. The default location is /path/to/stable-diffusion-webui/extensions/sd-dynamic-prompts/wildcards. It can also be manually defined in the main webui config.json under wildcard_dir. When in doubt, the help text for the extension in the webui lists the full path to WILDCARD_DIR

## Collections
The collections directory contains modifier libraries that you can use as is or to bootstrap your own. To get started, either use the Wildcard Manager tab to copy a one or more collections to your wildcards folder, or you can manually copy the files across. Three collections are bundled with the dynamic prompts extension.

- [jumbo](https://github.com/adieyal/sd-dynamic-prompts/tree/main/collections/jumbo)
- [parrotzone](https://github.com/adieyal/sd-dynamic-prompts/tree/main/collections/parrotzone)
- [devilkkw](https://github.com/adieyal/sd-dynamic-prompts/tree/main/collections/devilkkw)

Jumbo is a very large collection of wildcards across many categories including aesthetics, appearance, artists, medium, style, and time. It is a work in progress, but aims to provide good coverage of various modifier categories.

Parrotzone is a far smaller and more manageable collection sourced from https://proximacentaurib.notion.site/e28a4f8d97724f14a784a538b8589e7d?v=42948fd8f45c4d47a0edfc4b78937474.

Devilkkw focuses more on character building, clothes, gestures, food, etc

If you're using a Unix/Linux O/S, you can easily create a symlink to the relevant collection rather than copying it across if you don't plan to alter it. E.g.

	ln -sr collections/parrotzone wildcards/

You can also download additional extensions by running `python _tools/download_collections.py` from within the extension's root directory, i.e. `extensions/sd-dynamic-prompts/`

## Dynamic Prompts and Random Seeds
Random seeds play an important role in controlling the randomness of the generated outputs. Let's discuss how Dynamic Prompts works with random seeds in different scenarios.

### Without Dynamic Prompts Enabled

1. If the seed is set to -1: A random seed is picked. This seed is used to generate the first image, then the next image is created using seed + 1, and this pattern continues for subsequent images.
2. If the seed is set to a specific number greater than -1: The process is similar to the one above, but starts with the user-specified seed.
3. If the variation seed is defined, but variation strength is zero: The process remains the same as in the previous two points.
4. If the variation seed is set to a number greater than 0: Every image is generated using the same initial seed (randomly selected or set by the user). The variation seed is either random (if set to -1) or the value chosen by the user. The first image is generated with the variation seed, the next with variation seed + 1, and so on.

### Using With Dynamic Prompts Enabled in Random/Standard Mode:

1. If the seed is set to -1: The process is similar to the first point in the previous section. However, the prompt is also selected using the same seed (if the random prompt generator is used).
2. If the seed is set to a number greater than -1: The process is similar to the second point in the previous section. However, the difference is that a random prompt is also generated using the chosen seed (if the prompt generator is used).
3. If the fixed seed checkbox is checked: The same seed is used for all images and prompts. This means the same image is generated repeatedly (this is useful for combinatorial generation).
4. If both the fixed seed and unlink seed from prompt checkboxes are checked: A random seed is used for the prompt, but the same seed is used for all images. This setting can be useful if you want to see how different prompts affect the generation of the same image.

### Variation Seeds with Dynamic Prompts

1. Variation strength set to 0: Variations are ignored.
2. Variation set to a number > 0: A variation seed is assigned to every image, incrementing by one each time. However, only 1 prompt is generated since you are looking for variations of the same image.

### Combinatorial Mode with Variation Strength > 0
In this case, it only generates the first image for you, which is probably not what you want. To get the desired results, you might need to adjust the settings or use a different mode.
