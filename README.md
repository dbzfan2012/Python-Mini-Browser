CSE 493x 24sp Starter Code
============================

This repository is where you will build your browser.

Setup
-----

Clone this repository to your computer and then run the following
command to also download the autograder:

	git submodule update --init

If the autograder is ever updated, you can download the updates using:

	git submodule update --remote

That will make changes to the `.gitmodules` file; those changes are
safe to commit and push.

Work
----

Implement your web browser in `browser.py`. If you'd like, feel free
to split your browser into multiple files, as long as you import them
into `browser.py`, like this:

	from http import *
	from ui import *
	from layout import *
	...

Autograder
----------

Every time you push, the autograder will run. You can see the results
by clicking the Actions tab at the top of this page. If you click on
one of the runs on Actions page, you should see a grade summary at the
bottom of the page.

You can see more information about the autograder, and its test, in
[that repository](https://gitlab.cs.washington.edu/cse493x-24sp/cse493x-24sp-tests/).
