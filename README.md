# Dynamic Prompt templates

A custom script for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) to implement a tiny template language for random prompt generation. 

Using this script, the prompt:

	A {house|apartment|lodge|cottage} in {summer|winter|autumn|spring} by [2$$artist1|artist2|artist3]

Will any of the following prompts:

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



## Template syntax

### Variations
	{opt1|opt2|opt3}

This will randomly pick one of the options for every batch item.  In this case, "opt1" or "opt2" or "opt3"

### Combinations
	[2$$opt1|opt2|opt3]

This will randomly combine two of the options for every batch, separated with a comma.  In this case, "opt1, opt2" or "opt2, opt3", or "opt1, opt3" or the same pairs in the reverse order.

The prefix `2$$` can use any number between 1 and the total number of options you defined. If you omit the size prefix, then 2 will be used

### Nesting
Templates are processed in the following order:
1. variants
2. combinations
3. wildcards

This means that you can create more advanced templates. For example:

    I enjoy [2$${spaghetti|pizza|lasagne}|ice-cream|{tea|coffee}]

This will generate:
1. I enjoy pizza,tea
2. I enjoy spagetti,ice-cream

You can also nest within wildcards, e.g.

    {__seasons__|__timeofday__}

This will then either choose a season from seasons.txt or a time of day from timeofday.txt.

## Wildcard files
Wildcard files are not provided by this script as lists exists in other repositories. A good place to start looking is [here](https://github.com/jtkelm2/stable-diffusion-webui-1/tree/master/scripts/wildcards)

## WILDCARD_DIR
The script looks for wildcard files in WILDCARD_DIR. This is defined in the main webui config.json under wildcard_dir. If wildcard_dir is missing, then wildcard files should be placed in scripts/wildcards/
