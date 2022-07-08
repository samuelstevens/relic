# Literals

## Numbers

Numbers can only be specified as digits and a single period.

These are number literals: `200`, `0.01`, `4000.5`.

These are **not** number literals: `2e4`, `1e-5`, `1_000`, `2,000`, `.041`.

## Regular Expressions

Regular expressions are surrounding by vertical bars/pipes: `|`. This means that you can't use them in your regular expressions, which is a bit of pain in the ass. But I think it was worth it because the traditional delimiting character is `/`, and I was only using regular expressions to match against filepaths, and I didn't want to escape `/` every time in `path/to/data/file.txt`.

These are regular expressions: `|data/.*/0.txt|`.

These are **not** regular expressions: `|hello (world|sam)|`.

## Strings

Strings are surrounded by single quotes. They cannot be escaped.

These are string literals: `'hello'`, `'100.12'`, `'my name is'`.

These are **not** string literals: `'can\'t'`, `"hello"`.

## Values

`True`, `False` and `None` are all keywords in the Relic query language. Most of the time, you will not need `True` or `False` because you can simply use `<expr>` and `(not <expr>)`, respectively.
