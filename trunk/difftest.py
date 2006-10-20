#!/usr/bin/env python

import difflib

a = ["Hello World!", "You suck!", "What am I talking", "Sometime", "Nothing"]
b = ["Hello World!", "You're great!", "You suck!", "What am I talking", "Nothing"]

seq_matcher = difflib.SequenceMatcher()
seq_matcher.set_seqs(a, b)
print seq_matcher.get_opcodes()
