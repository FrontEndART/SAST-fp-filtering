# Element Extractor

This is a simple python tool aimed to extract specific source code elements based on ranges.

## Prerequisites

- Python 3.10 + pip
- pipenv

## Setup

In the project root:

```bash
pipenv install
```

To get information about running the tool:

```bash
python main.py --help
```


## Example run

Consider the Java file [```./your_java_file.java```](./your_java_file.java).
Suppose we know lines 5-9 and 17 were modified as part of a change. Our tool will find the methods changed as part of this modification:

- lines 5-9: main, addNumbers
- line 17: addNumbers


Finding methods are modified if the changes happened in positions 5:1-9:1 and 17:1-17:5. (line:col) can be done as:

```bash
pipenv shell
python main.py --file your_java_file.java --ranges 5:1-9:1,17:1-17:5
```

Then the result will be as follows:

```bash
{CodeRange(17:1-17:5): [CodeElement(range=CodeRange(16:5-18:6),
                                    id='calculateArea',
                                    type='method_declaration')],
 CodeRange(5:1-9:1): [CodeElement(range=CodeRange(3:5-6:6),
                                  id='main',
                                  type='method_declaration'),
                      CodeElement(range=CodeRange(8:5-10:6),
                                  id='addNumbers',
                                  type='method_declaration')]}
```

The tool can be run to parse any AST node (not just method declarations) that TreeSitter supports. 