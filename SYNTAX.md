# Template syntax

## Combinations
	{2$$opt1|opt2|opt3}

This will randomly combine two of the options for every batch, separated with a comma.  In this case, "opt1, opt2" or "opt2, opt3", or "opt1, opt3" or the same pairs in the reverse order.

	{1-3$$opt1|opt2|opt3}

This will use a random number of options between 1 and 3 for each batch. 

If the number of combinations chosen is greater than the number of options listed then options may be repeated in the output.
If the number of combinations chosen is less than or equal to the number of options listed then the same options will not be chosen more than once.

	{4$$and$$opt1|opt2|opt3|opt4|opt5}

This will choose 4 options and join them together with 'and' instead of the default comma. When there are multiple $$ tokens then the first item is the number of options to choose and the second option is the joiner to use.
	{-$$opt1|opt2|opt3}

An omitted minimum is assumed to be 0 and an omitted maximum is assumed to be the number of options.


	{opt1|opt2|opt3}
    
If you omit the $$ prefix, one item will be selected. (Equivalent to 1$$)

Options are chosen randomly with replacement. This means that {2$$opt1|opt2} can return any of the following:
- opt1, opt1
- opt1, opt2
- opt2, opt1
- opt2, opt2

This is useful in conjunction with wildcards (see below).


Options can be assigned relative weights using a :: prefix operator.

	photo of a {3::blue|red} ball

This will generate 3 photos of a blue ball per every 1 photo of a red ball.

<img src="images/weighting-colours.png">

	photo of a {blue|0.25::red} ball
	
Decimals also work as expected: this will generate 4 photos of a blue ball per every 1 photo of a red ball.

	photo portrait of a {59::white|21::latino|14::black|8::asian} {man|woman}

This would generate photo portraits of men and women of different races, proportional to the 2020 U.S. census.
<img src="images/weighting-us-population.png">

If you omit the :: prefix, it will have a default weight of 1.0. (Equivalent to 1::prompt)

## Wildcard files
Wildcards are text files (ending in .txt). Each line contains a term, artist name, or modifier. The wildcard file can then be embedded in your prompt by removing the .txt extension and surrounding it with double underscores. e.g:

	My favourite colour is __colours__

Empty lines and lines starting with `#` are ignored. This can be used to add comments or disable sections of the file.

Mixing Combinations and Wildcards can be useful. For example,

	a photo of a {2-4$$and$$__adjective__} house

will choose between 2 and 4 options from adjective.txt, join them together with "and", for results such as "a photo of a cozy and ancient and delicate house"


## Nesting
You can nest inside combinations. This means that you can create more advanced templates. For example:

    {__seasons__|__timeofday__}

This will then either choose a season from seasons.txt or a time of day from timeofday.txt.

Combinations can also be nested inside other combinations, e.g. 

    {{a|b|c}|d}


## Recursion
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

## Comments
Python and c-style comments are supported:

    Test string
    # This  a comment until the end of the line
    // this is also a comment until the end of the line
    {A|/* this is an inline comment */B}

## Whitespace
In most cases, whitespace is ignored which allows you to create more expressive and readable prompts, e.g.

	wisdom {
    	woman, __colours__ eyes, braided hair
    	|man using a __war/weapons/swords/european__, red turban
    	|dwarf weilding a warhammer, __colours__ beard
	}, 
	knows the meaning of life, warrior, hyper-realistic, peaceful, dark fantasy, unreal engine, 8k