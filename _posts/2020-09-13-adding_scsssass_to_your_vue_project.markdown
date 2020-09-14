---
layout: post
title: Adding SCSS/SASS to your Vue project
date: 2020-09-13 17:37:37 -0800
comments: true
---

# Adding SCSS/SASS to your Vue project

You may have noticed yourself copying colors and other style information between Single File Vue components, and wondering if there was a way to avoid repeating oneself in each component.

**Shouldn't we be able to declare simple things like colors, typography, and common widgets like buttons in a single place, to be shared globally with all Vue components?**

Well, [SASS](https://en.wikipedia.org/wiki/Sass_(stylesheet_language)) (Syntactically Awesome Style Sheets) is a well-known CSS language extension since 2006.  It has two syntaxes, and the more popular Sassy CSS (SCSS) syntax is closer to traditional CSS and is what I'll be describing here.

## A Quick Primer
A quick tour of SCSS: w3schools has a [basic tutorial](*%20[https://www.w3schools.com/sass/default.asp]%0A) that is decent for the first 8 sections.  Once it gets into functions the quality drops off for lack of examples so stop after the first 8 sections.

Let's quickly review three of the most significant SCSS syntax elements give us:
- referring to variables
- nested selector syntax
- & parent reference

In example below ([and on JSFiddle](https://jsfiddle.net/stevenatkinson/a5o4vbze/41/)), if we were displaying cards on the screen with HTML such as:
```html
<div class="cards">
  <div class="card diamond">
   5 of Diamonds
  </div>
    <div class="card club">
   5 of Clubs
  </div>
</div>
```

then we could share colors and target elements in CSS using new syntax:

```swift

/* Colors and sizes */
$text-color: white;
$border-color: black;
$border-size: 3px;

$card-color-1: red;
$card-color-2: black;

/* Match the outer element */
.cards {

   /* Refer to colors by name */
   color: $text-color;

  .card {
     width: 200px;
     height: 200px;
     margin: 5px;
     border: $border-size solid $border-color;
  }

  .diamond, .heart {
     background-color: $card-color-1;
  }

  .club, .spade {
   width: 200px;
     background-color: $card-color-2;
  }

  /* Refer to the parent element using & */
  &:hover {
    /* Use functions to make new colors! */
    color: darken($text-color, 20%);
  }
}

```

# How do I add SASS/SCSS to Vue?

Let's tell the Vue project that we are going to use javascript modules `node-sass` and the `sass-loader`.  These packages will translate SCSS into pure CSS when we build our project - that's what loaders do.

Go to your Vue project folder, and run:

```bash
npm install --save-dev node-sass sass-loader
```

We are now free to use a `lang="scss"` directive in our view and components:
```html
<style lang="scss" scoped>
...
</style>
```

Now you can style your HTML templates using the SCSS syntax!

# How do we approach using SCSS with Vue?

The convention is that all style files belong in the `src/styles` folder.  Make that folder if it does not exist.

Let's create two files in a new `styles` folder.

* `_variables.scss`: will contain color declarations
* `_widgets.scss`: will contain styles for global elements such as buttons

These files start with underscore (\_) as a convention since they are global in scope.

Variables should contain color and other interesting variables:
```js
$link-primary: blue;
$link-secondary: purple;


$color-1: #71b869;
$color-2: #979797;
$color-3: #303216;
$color-4: #4a90e2;

$background-1: #ebf2e2;

$border-1: #9e9393;

$global-radius: 4px;
```

Widgets should contain common styles for links and buttons, and should also contain form details.
```js
/* Links */


a {
  input[type='submit'] {
    color: $link-primary;
  }
  &:visited {
    input[type='submit'] {
      color: $link-primary;
    };
  }
}


a {
  &:hover { color: $link-secondary }
  &:active { color: $link-secondary }
}

/* Form elements */
input[type='submit'] {
  color: $link-primary;
}

input[type='submit']:hover,
ul.buttons a:hover {
  color: $link-secondary;
}


/* Buttons */

button,
a.button,
.button {
  border: 1px solid $color-2;
  font-weight: bold;
  font-size: 13px;
  color: $color-1;
  text-align: center;
  width: 11.8em;
  height: 2em;

  &:hover {
    background-color: $color-1;
    color: white;
    font-weight: normal;
  }
}
```

Once you have those files, create an `App.scss` in the `styles` folder that imports those files:
```js
@import 'src/styles/variables';
@import 'src/styles/widgets';
...
// any further global resets or styles
...

```

A fuller example site showing how these techniques are used is available on Github in the [sass-simple branch](https://github.com/nowucca/greater-goods-client/tree/sass-simple) of the greater-goods-grocery client.

# Challenge
......and a question I still have:

It seems there is a tension between global SCSS rules, splitting things into scoped Vue components and generating efficient code using webpack. What is a reasonable way to manage your  scss files and still get advantages of webpack and Vue components?

You may find the following articles food for thought:
* [https://css-tricks.com/how-to-import-a-sass-file-into-every-vue-component-in-an-app/](https://css-tricks.com/how-to-import-a-sass-file-into-every-vue-component-in-an-app/)
* [https://medium.com/@osternaud\_clem/organize-your-sass-files-b2c2513f3fcf](https://medium.com/@osternaud_clem/organize-your-sass-files-b2c2513f3fcf)