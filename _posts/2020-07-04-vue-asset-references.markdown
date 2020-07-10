---
layout: post
title:  "JavaScript and Vue Asset References should be improved"
date:   2020-07-04
comments: true
---

In the context of the [Vue](vuejs.org) framework, javascript's `require` and images...

From research into Vue for teaching, I've determined that when referring to CSS or image assets, it is best to
ALWAYS use "@" notation for referring to images.


| Purpose | Example Syntax |
---: | :---
| For static image references in templates | `src="@/assets/images/site/cr-facebook-icon.jpeg"`
| For dynamic image references in templates |  `:src="require('@/assets/images/products/' + productImageFileName(book))"`
| To import css in JavaScript | `import "@/assets/css/normalize-and-reset.css";`
| To import css in `style` of a Vue component | `@import '~@/assets/css/normalize-and-reset.css';`
| To have a static background image in `css`|  `  background-image: url('~@/assets/site/neonbrand-394691-unsplash.jpg');`


Perhaps the next language level up we can be smarter about these pecadillos.

