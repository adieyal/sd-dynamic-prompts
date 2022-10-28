# Dynamic Prompt templates

A custom script for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) to implement a tiny template language for random prompt generation. 

Using this script, the prompt:

	A {house|apartment|lodge|cottage} in {summer|winter|autumn|spring} by {2$$artist1|artist2|artist3}

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

### Combinations
	{2$$opt1|opt2|opt3}

This will randomly combine two of the options for every batch, separated with a comma.  In this case, "opt1, opt2" or "opt2, opt3", or "opt1, opt3" or the same pairs in the reverse order.

	{1-3$$opt1|opt2|opt3}

This will use a random number of options between 1 and 3 for each batch. 

	{opt1|opt2|opt3}
If you omit the $$ prefix, one item will be selected. (Equivalent to 1$$)

### Wildcard files
Wildcard files are not provided by this script as lists exists in other repositories. A good place to start looking is [here](https://github.com/jtkelm2/stable-diffusion-webui-1/tree/master/scripts/wildcards)
Empty lines and lines starting with `#` are ignored. This can be used to add comments or disable sections of the file.

### Nesting
You can nest combinations inside wildcards. This means that you can create more advanced templates. For example:

    {__seasons__|__timeofday__}

This will then either choose a season from seasons.txt or a time of day from timeofday.txt.

### Recursion
Prompts are processed recursively. If a wildcard file contains a row with dynamic syntax, then that will be resolved as well. For example if seasons.txt contains the following rows:

	Summer
	Winter
	{Autumn|Fall}
	Spring

if the 3rd row is chosen, then either Autumn or Fall will be selected. You could go pretty wild e.g.

	Summer
	__winter_in_different_languages__
	{Autumn|Fall}
	Spring

## Fuzzy Glob/recursive wildcard file/directory matching
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

## WILDCARD_DIR
The script looks for wildcard files in WILDCARD_DIR. This is defined in the main webui config.json under wildcard_dir. If wildcard_dir is missing, then wildcard files should be placed in scripts/wildcards/
