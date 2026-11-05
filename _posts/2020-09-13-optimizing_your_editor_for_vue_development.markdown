---
layout: post
title: Optimizing your Editor for Vue Development
date: 2020-09-13 15:40:33 -0800
comments: true
---

# Optimizing your Editor for Vue Development

For mature frameworks such as Vue.js, it can be very beneficial to spend a little time setting up your editing tools to make development more productive.

I use two major tools for Vue.js development:
* IntelliJ IDEA for editing with the Vue.js plugin,
* the popular real-world editor called  ["VS Code"](https://code.visualstudio.com/Download) from Microsoft.

For each of these editing tools there are some tips to establish a productive environment for editing Vue files.

The goals of these tips are:
* establishing syntax highlighting
* automatic formatting when you save a file
* optionally, accessing text "shortcuts" to avoid typing the same things over and over.

It may sound silly, but with the amount of coding a develop using Vue.js is doing, no matter which tool you use your productivity gain will be worth it if you follow the steps for your editor.

## Common tips to all editors

* You can use [`Emmet`-style html shortcuts](https://docs.emmet.io/cheat-sheet/).  For example, type `ul>li` and hit tab - your text will automatically expand to:
	```html
	<ul>
	  <li></li>
	</ul>
	```

* Create a [.editorconfig file](https://editorconfig.org/) at the top level of your client and server projects.  This is a new standard across editors to control things like indents and whitespaces.  My settings are:

	```js
	root = true
	[*]
	charset = utf-8
	end_of_line = lf
	indent_size = 2
	indent_style = space
	insert_final_newline = true
	trim_trailing_whitespace = true
	max_line_length = 120
	tab_width = 4

	[*.vue]
	tab_width = 2

	```

* For either editor install [Sarah Drasner's Vue shortcuts](https://marketplace.visualstudio.com/items?itemName=sdras.vue-vscode-snippets).  These are supported in IntelliJ already ([see here ](https://www.jetbrains.com/help/idea/vue-js.html#ws_vue_live_templates), or just use Cmd-J (Mac) or Ctrl-J (Windows) at the top of a .vue file to see all the options).  These were designed for Visual Studio as well at the link above.  If you have trouble I can help install these.

## VS Code Tips

For this course, I strongly recommend [watching the video and reading the transcript](https://www.vuemastery.com/courses/real-world-vue-js/optimizing-your-editor) for editor setup from Vue Mastery.  It should take under 20 minutes.

This shows how to establish Prettier for automatic syntax changes on Save.

## IntelliJ IDEA Tips

Read the [summary of Vue.js plugin capabilities here](https://www.jetbrains.com/help/idea/vue-js.html) to get a feel for everything IntelliJ's Vue plugin can offer.

Install the Prettier plugin for IntelliJ.

Assuming you have set up a standard project, open IntelliJ Preferences and
* Set up your eslint tool

![ESLint Setup](/images/eslint-setup.png ){: width="500" }

* and then also set up the Prettier tool

![Prettier Setup](/images/prettier-setup.png ){: width="500" }

This will see ESLint highlight mistakes during typing, and both work together to format and fix issues when a file is saved.
