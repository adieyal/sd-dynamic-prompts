# Dynamic Prompt templates

A custom script for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) to implement a tiny template language for random prompt generation. This snippet of code originated in a Disco Diffusion colab and has also found its way into many Stable Diffusion colabs. 

Using this script, the prompt:

	A {house|apartment|lodge|cottage} in {summer|winter|autumn|spring} by [2$$artist1|artist2|artist3] will any of the following prompts:

- A **house** in **summer** by **artist1**, **artist2**
- A **lodge** in **autumn** by **artist3**, **artist1**
- A **cottage** in **winter** by **artist2**, **artist3**
...


This is especially useful if you are searching for interesting combinations of artists and styles.

## Template syntax

### Variations
	{opt1|opt2|opt3}

This will randomly pick one of the options for every batch item.  In this case, "opt1" or "opt2" or "opt3"

### Combinations
	[2$$opt1|opt2|opt3]

This will randomly combine two of the options for every batch, separated with a comma.  In this case, "opt1, opt2" or "opt2, opt3", or "opt1, opt3" or the same pairs in the reverse order.

The prefix `2$$` can use any number between 1 and the total number of options you defined. If you omit the size prefix, the number of options combined will be defined randomly

### Nesting
You can have variations inside combinations but not the other way round (for now)

Example:

	I love[ {red|white} wine | {layered|chocolate} cake | {german|belgian} beer]
