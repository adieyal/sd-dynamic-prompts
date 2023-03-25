// mouseover tooltips for various UI elements

// Declare a dictionary with pairs: "UI element label"="Tooltip text".
var dynamic_prompting_titles = {
"Dynamic Prompts enabled": "Disable dynamic prompts by unchecking this box.",

"Combinatorial generation": `
Instead of generating random prompts from a template, combinatorial generation produces every possible prompt from the given string.
The prompt 'I {love|hate} {New York|Chicago} in {June|July|August}' will produce 12 variants in total.

The value of the 'Seed' field is only used for the first image. To change this, look for 'Fixed seed' in the 'Advanced options' section.`.trim(),

"Max generations (0 = all combinations - the batch count value is ignored)": `
Limit the maximum number of prompts generated. 0 (default) will generate all images. Useful to prevent an unexpected combinatorial explosion.
`.trim(),

"Combinatorial batches": `
Re-run your combinatorial batch this many times with a different seed each time.
`.trim(),

"Magic prompt": `
Magic Prompt adds interesting modifiers to your prompt for a little bit of extra spice.
The first time you use it, the MagicPrompt model is downloaded so be patient.
If you're running low on VRAM, you might get a CUDA error.`.trim(),

"Max magic prompt length": "Controls the maximum length in tokens of the generated prompt.",
"Magic prompt creativity": "Adjusts the generated prompt. You will need to experiment with this setting.",
"Magic Prompt batch size": "The number of prompts to generate per batch. Increasing this can speed up prompt generation at the expense of slightly increased VRAM usage.",

"I'm feeling lucky": `
Uses the lexica.art API to create random prompts.
The prompt in the main prompt box is used as a search string.
Leaving the prompt box blank returns a list of completely randomly chosen prompts.
Try it out, it can be quite fun.
`.trim(),

"Attention grabber": `Randomly selects a keyword from the prompt and adds emphasis to it. Try this with Fixed Seed enabled.`.trim(),

"Write prompts to file": `
The generated file is a slugified version of the prompt and can be found in the same directory as the generated images.
E.g. in ./outputs/txt2img-images/.`.trim(),

"Don't generate images": "Be sure to check the 'Write prompts to file' checkbox if you don't want to lose the generated prompts. Note, one image is still generated.",
"Enable Jinja2 templates": "Jinja2 templates are an expressive alternative to the standard syntax. See the Help section below for instructions.",
"Unlink seed from prompt": "Check this if you want to generate random prompts, even if your seed is fixed",
"Don't apply to negative prompts": "Don't use prompt magic on negative prompts.",

"Fixed seed": `
Select this if you want to use the same seed for every generated image.
This is useful if you want to test prompt variations while using the same seed.
If there are no wildcards then all the images will be identical.
`.trim(),
"Write raw prompt to image": "Write the prompt template into the image metadata"
};

// Combine two dictionaries: the original (titles) and our new (dynamic_prompting_titles) into one
//  and assign it to the original "titles" variable. The original "hints.js" script will do all the magic.
titles = Object.assign({}, titles, dynamic_prompting_titles);
