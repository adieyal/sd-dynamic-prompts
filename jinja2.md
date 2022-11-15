# Jinja2 templates
Jinja2 templates is an experimental feature that enables you to write prompts with an expressive templating language. This is an advanced feature and is only recommended for users who are comfortable writing scripts.

To enable the feature, open the advanced accordion and select __Enable Jinja2 templates__.
<img src="images/jinja_templates.png">

Here are some examples of what you can do with Jinja2 templates
### Literals
Literal strings work as expected:

    I love red roses

### Random choices
Similar to the standard `{A|B|C}` syntax

    I love {{ choice('red', 'blue', 'green') }} roses
    
This will create one prompt and randomly choose one of the three colors.

### [Iterations](https://jinja.palletsprojects.com/en/3.1.x/templates/#for)

    {% for colour in ['red', 'blue', 'green'] %}
        {% prompt %}I love {{ colour }} roses{% endprompt %}
    {% endfor %}

This will produce three prompts, one for each color. The prompt tag is used to mark the text that will be used as the prompt. If no prompt tag is present then only one prompt is assumed

### Wildcards
Similar to the standard wildcard syntax

    {% for colour in wildcard("__colours__") %}
        {% prompt %}I love {{ colour }} roses{% endprompt %}
    {% endfor %}

This will produce one prompt for each colour in the wildcard.txt file.

### [Conditionals](https://jinja.palletsprojects.com/en/3.1.x/templates/#if)

    {% for colour in ["red", "blue", "green"] %}
        {% if colour == "red"}
            {% prompt %}I love {{ colour }} roses{% endprompt %}
        {% else %}
            {% prompt %}I hate {{ colour }} roses{% endprompt %}
        {% endif %}
    {% endfor %}

This will produce the following prompts:
* I love red roses
* I hate blue roses
* I hate green roses

These are trivial examples but the Jinja2 template language is very expressive. You can use it to develop sophisticated prompt templates. For more information see the <a href="https://jinja.palletsprojects.com/en/3.1.x/templates/">Jinja2 documentation.</a>.

### [Setting variables](https://jinja.palletsprojects.com/en/3.1.x/templates/#with-statement)
You can create a variable for further re-use, e.g.

	{% with careers = ['doctor', 'lawyer', 'accountant'] %}
		{% for career1 in careers %}
			{% for career2 in careers %}
				{% if career1 != career2 %}
					{% prompt %}professional digital airbrush art of A {{ career1 }} and {{ career2 }}{% endprompt %}
				{% endif %}
			{% endfor %}
		{% endfor %}
	{% endwith %}

the careers array is now avaible inside the {% with %} ... {% endwith %} block.

### Additional functions

#### Random

    This is a random number: {{ random() }}

e.g. This is a random number: 0.694942884614521

### Random Integer

	My favourite number is {{ randint(1, 10) }}

e.g. My favourite number is 6

### [Range](https://jinja.palletsprojects.com/en/3.1.x/templates/#jinja-globals.range)
Return a list containing an arithmetic progression of integers.

    {% for i in range(10) %}{{ i }}{% endfor %}

Returns
`0123456789`

You can specify a start and stop

    {% for i in range(5,9) %}{{ i }}{% endfor %}

Returns
`5678`

Finally, you can provide an optional step:

    {% for i in range(0,10, 2) %}{{ i }}{% endfor %}

Returns
`02468`

### Weighted selection

	My favourite colour is {{ weighted_choice(("pink", 0.2), ("yellow", 0.3), ("black", 0.4), ("purple", 0.1)) }}

Will select one of the colours according to their weight, i.e. pink 20% of the time, yellow 30% of the time, etc

### Permutations

	Generate all the possible permutations of elements in a list


	{% for val in permutations(["red", "green", "blue"], 2) %}
		{% prompt %}My favourite colours are {{ val|join(' and ') }}{% endprompt %}
	{% endfor %}

My favourite colours are red and green
My favourite colours are red and blue
My favourite colours are green and red
My favourite colours are green and blue
My favourite colours are blue and red
My favourite colours are blue and green

## [Filters](https://jinja.palletsprojects.com/en/3.1.x/templates/#filters)
Variables can be modified by filters. Filters are separated from the variable by a pipe symbol (`|`) and may have optional arguments in parentheses. Multiple filters can be chained. The output of one filter is applied to the next.

Here are a few useful filters:
### [Join](https://jinja.palletsprojects.com/en/3.1.x/templates/#jinja-filters.join)

    {% with colours = ['red', 'blue', 'green'] %}
        {{ colours|join(' and ') }}
    {% endwith %}

This joins an array with a separator, in this case: `red and blue and green`

### [Length](https://jinja.palletsprojects.com/en/3.1.x/templates/#jinja-filters.length)
    {% with colours = ['red', 'blue', 'green'] %}
        There are {{ colours|length }} colours in the array
    {% endwith %}

Returns the number of elements in an array

### [Replace](https://jinja.palletsprojects.com/en/3.1.x/templates/#jinja-filters.replace)
    {{ 'some_string'|replace('_', '-') }}

Replaces `_` with `-` and returns `some-string`


### [Sort](https://jinja.palletsprojects.com/en/3.1.x/templates/#jinja-filters.sort)

    {% with colours = ['red', 'blue', 'green'] %}
        {{ colours|sort|join(' and ') }}
    {% endwith %}

Does what it say on the box, it sorts elements of an array: `blue and green and red`

You can find more fitlers [here](https://jinja.palletsprojects.com/en/3.1.x/templates/#jinja-filters).


## Batch count

Note: Batch count works differently when using Jinja2 templates. If you set __Batch count__ to 1 and __Batch size__ to 1 and use this prompt:

	{% for colour in ['blue', 'red', 'green'] %}
	    {% prompt %}I love {{ colour }} roses{% endprompt %}
	{% endfor %}

You will produce 3 images. This is due to the fact that {% prompt %}...{% endprompt %} creates one prompt for each colour. If you set __Batch count__ to 2, 6 images will be created. The __Combinatorial batches__ slider is also ignored since you can achieve the same effect as above by creating mulitple prompts in your template and then increasing __Batch count__.

If you are using these templates, please let me know if they are useful.

## Cookbook

### [Prompt Editing](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features#prompt-editing)

	{% for i in range(11) %}
		{% prompt %}[dog:cat:{{ i/10 }}]{% endprompt %}
	{% endfor %}

Using Automatic1111's prompt editing feature, these prompts are generated:
```
[dog:cat:0]
[dog:cat:0.1]
[dog:cat:0.2]
[dog:cat:0.3]
[dog:cat:0.4]
[dog:cat:0.5]
[dog:cat:0.6]
[dog:cat:0.7]
[dog:cat:0.8]
[dog:cat:0.9]
[dog:cat:1]
```
Automatic1111 will render with dog for the first x% of steps, and then switch to using cat.
