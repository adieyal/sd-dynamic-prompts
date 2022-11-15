// mouseover tooltips for various UI elements

// Declare a dictionary with pairs: "UI element label"="Tooltip text".
var dynamic_prompting_titles = {
	"Combinatorial generation": "Instead of generating random prompts from a template, combinatorial generation produces every possible prompt from the given string.\nThe prompt 'I {love|hate} {New York|Chicago} in {June|July|August}' will produce 12 variants in total.\nDon't forget to increase the 'Batch count'/'Batch size' value accordingly.\n\nThe value of the 'Seed' field is only used for the first image. To change this, look for 'Fixed seed' in the 'Advanced options' section.",
	"Combinatorial batches": "Re-run your combinatorial batch that many times with a different seed.\nThe maximum number of outputs = Combinatorial batches * Batch size * Batch count.\nTo specify number of wanted prompt combinations use 'Batch count'/'Batch size' options.",
	"Magic prompt": "The first time you use it, the MagicPrompt model is downloaded.\nIf you're low in VRAM, you might get a CUDA error.",
	"Max magic prompt length": "Controls the maximum length in tokens of the generated prompt.",
	"Magic prompt creativity": "Adjusts the generated prompt but you will need to experiment with this setting.",
	"I'm feeling lucky": "Uses the lexica.art API to create random prompts. The prompt in the main prompt box is used as a search string.\nLeaving the prompt box blank returns a list of completely randomly chosen prompts.",
	"Write prompts to file": "The generated file is a slugified version of the prompt and can be found in the same directory as the generated images.\nE.g. in ./outputs/txt2img-images/.",
	"Don't generate images": "Enable the 'Write prompts to file' checkbox if you don't want to lose the generated prompts.",
	"Enable Jinja2 templates": "See the Help section below for instructions.",
	"Unlink seed from prompt": "",
	"Disable negative prompt": "",
	"Fixed seed": "Select this if you want to use the same seed for every generated image.\nIf there are no wildcards then all the images will be identical.",
};

// Combine two dictionaries: the original (titles) and our new (dynamic_prompting_titles) into one
//  and assign it to the original "titles" variable. The original "hints.js" script will do all the magic.
titles = Object.assign({}, titles, dynamic_prompting_titles);
