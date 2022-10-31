# Stable Diffusion Dynamic Prompts extension 

A custom extension for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) that implements an expressive template language for random or combinatorial prompt generation along with features to support deep wildcard directory structures.

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

## Installation

*Note* dynamic prompting is now an extension. To install, run the following command from within the webui directory:

	git clone https://github.com/adieyal/sd-dynamic-prompting/ extensions/dynamic-prompts

If you are upgrading from a version prior to 0.11.0, be sure to delete the old dynamic_promting.py from the webui's scripts directory and the old dynamic_prompting.js from the webui's javascript directory.


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

### Combinatorial Generation
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

You also arbitrarily nest combinations inside wildcards and wildcards in combinations.

Combinatorial generation can be useful if you want to create an image for every artist in a file. It can be enabled by checking the __Combinatorial generation__ checkbox in the ui. Note, __num batches__ changes meaning. With random generation, exactly __num_batches__ * __batch_size__ images are created. With combinatorial generation, at *most* __num_batches__ * __batch_size__ images are created. This upper limit ensures that you don't accidentially create a template that unexpectedly  produces thousands of images.

Combinations are not yet supported, i.e. `{2$$a|b|c}` will treat `2$$a` as one of the options instead of selecting two of a, b and c.

The combinatorial batches slider lets you repeat the same set of prompts a number of times with different seeds. The default number of batches is 1.

## Fixed seed
Select this if you want to use the same seed for every generated image. If there are no wildcards then all the images will be identical. It is useful if you want to test the effect of a particular modifier. For example:

	A beautiful day at the beach __medium/photography/filmtypes__

That way you can isolate the effect of each film type on a particular scene. Here are some of the results:
<img src="images/filmtypes.jpg"/>

## Magic Prompt
Using [Gustavosta](https://huggingface.co/Gustavosta/MagicPrompt-Stable-Diffusion)'s MagicPrompt model, automatically generate neww prompts from the input. Trained on 80,000 prompts from [Lexica.art](lexica.art), it can help give you interesting new prompts on a given subject. Here are some automatically generated variations for "dogs playing football":

> dogs playing football, in the streets of a japanese town at night, with people watching in wonder, in the style of studio ghibli and makoto shinkai, highly detailed digital art, trending on artstation

> dogs playing football, in the background is a nuclear explosion. photorealism. hq. hyper. realistic. 4 k. award winning.

> dogs playing football, in the background is a nuclear explosion. photorealistic. realism. 4 k wideshot. cinematic. unreal engine. artgerm. marc simonetti. jc leyendecker

This is compatible with the wildcard syntax described above.


The first time you use it, the model is downloaded. It is approximately 500mb and so will take some time depending on how fast your connection is. It will also take a few seconds on first activation as the model is loaded into memory. Note, if you're low in VRAM, you might get a Cuda error. My GPU uses less than 8GB by YMMV.

## Collections 
The collections directory contains modifier libraries that you can use as is or use to bootstrap your own. Copy the collection that you want to use into the wildcards directory. Note, in previous versions, the collections were in the wildcards directory. This has now changed so that your own collections don't get clobbered every time you want to update the extension.


## WILDCARD_DIR
The script looks for wildcard files in WILDCARD_DIR. This is defined in the main webui config.json under wildcard_dir. If wildcard_dir is missing, then wildcard files should be placed in scripts/wildcards/

## Contributing
If you're interested in contributing to the development of this extension, here are some features I would like to implement:

1. **Saved templates** - [publicprompts.art](https://publicprompts.art/) produces great prompt templates. e.g. 

> Funky pop Yoda figurine, made of plastic, product studio shot, on a white background, diffused lighting, centered

You can swap out Yoda for anything to create a great character. If I create/discover a great prompt that can be turned into a template, it would be great to have a place to save it. The extension could provide some initial templates. Users could then create and save their own.

2. **Tag-based modifers**. Creating a strict taxonomy of concepts for modifiers is always going to be flawed. Some modifiers fit in multiple categories. It would be better to introduce tags to make it easy to place modifiers in multiple places at once.

3. **Improved modifier management**. The modifier library is a little clunky at the moment. You can find a nested hierarchy of all wildcard files, but it isn't possible to see what's in them or even edit them from within the interface. It might be best to implement this in a separate tab.

4. **Improve the modifier library**. I'm currently creating the library from multiple sources but building taxonomies is hard, especially if you're not a domain expert. The photography section is a good example, there are wildcard files for lighting, filetypes, camera models, perspective, photo websites, etc. Someone with a better understanding of photography might have a better way to divide this. The artists section in particular needs some TLC.

5. **Option tweaking**. There have been a few requests for option tweaking like XY Plot. I'm not sure that that is in scope for this extension, but it would be nice to see if we could find a solution that leverage's XY Plot.

6. **Improved UI**. The current UI works, but a few javascript tweaks could improve the user experience tremendously.

Let me know if there is anything you would be interested in looking into.
