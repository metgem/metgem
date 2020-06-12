.. _pandas-eval: https://pandas.pydata.org/pandas-docs/stable/user_guide/enhancingperf.html#supported-syntax

.. |add| image:: /images/add.png
.. |remove| image:: /images/remove.png
.. |functions| image:: /images/formulae-functions.png
.. |constants| image:: /images/formulae-constants.png
.. |operators| image:: /images/formulae-operators.png

.. _tools_formulae:

Formulae
********

.. image:: /images/add-columns-by-formulae.png

This tools is designed to allow you to combine multiple columns using simple or complex formulae. See :ref:`formulae_usage` for pratical informations and :ref:`formulae_syntax` to get a description of the formulae's syntax.
        
.. _formulae_usage:
    
Usage
~~~~~

The window is divided in two parts:

    * `Available columns`: on the left lies a table of the metadata columns used to create aliases for metadata columns titles,
    * `Mappings`: on the right, you can create new columns by combining existing ones.
    
Creating a new formula will then need two steps:
    #. To be used in a formula, a column need an alias (that need to be a valid Python_ :ref:`identifier <python_identifier>`). You just need to double-click inside a cell of the `Alias` column to define an alias for the corresponding column. Validate by hitting :kbd:`Enter`.
    #. Last step is to add a new column by clicking on the |add|, set it's name (a column with this name will be overwritten if it already exists) and define a formula thats includes constants and/or alias set in step before.
    
Toolbar
~~~~~~~

The toolbar located on top right of the dialog includes a few buttons:

    * |add| `Add new formula`: Add a new empty line in the `Mappings` table. It's up to you to fill `Name` and `Formula` cells,
    * |remove| `Remove selected formulae`: Remove the selected rows on the `Mappings` table.
    * |functions| `Add Function`: A drop-down sectional list of available functions. A function is used by adding a comma-separated list of arguments in parentheses after it's name, e.g. ``mean(a,b)``.
    * |constants| `Add Constant`: A list of available constants. A constant is just a replacement for

.. _formulae_syntax:

Syntax
~~~~~~

The syntax used to describe formulae is a subset of Python_ programming language. As |appname| use the Pandas_ library internally, the following operations are supported:

    * Arithmetic operations except for the left shift (``<<``) and right shift (``>>``) operators, e.g., ``x + 2 * pi / y ** 4 % 42 - pi``
    * Comparison operations, including chained comparisons, e.g., ``2 < x < y``
    * Boolean operations, e.g., ``x < y`` and ``x < y`` or ``not column1``
    * List and tuple literals, e.g., ``[1, 2]`` or ``(1, 2)``
    * Math functions: ``sum``, ``mean``, ``median``, ``prod``, ``std``, ``var``, ``quantile``, ``min``, ``max``, ``sin``, ``cos``, ``exp``, ``log``, ``expm1``, ``log1p``, ``sqrt``, ``sinh``, ``cosh``, ``tanh``, ``arcsin``, ``arccos``, ``arctan``, ``arccosh``, ``arcsinh``, ``arctanh``, ``abs``, ``arctan2`` and ``log10``
    * Constants: ``pi``, ``e``

This Python syntax is not allowed:

    * Expressions:
        - Function calls other than math functions.
        - is/is not operations
        - if expressions
        - lambda expressions
        - list/set/dict comprehensions
        - Literal dict and set expressions
        - yield expressions
        - Generator expressions
        - Boolean expressions consisting of only scalar values
        - Attribute access, e.g., ``df.a``
        - Subscript expressions, e.g., ``df[0]``
        
    * Statements
        - Neither simple nor compound statements are allowed. This includes things like for, while, and if.

.. _python_identifier:

.. note:: A Python identifier is a name used to identify a variable, function, class, module or other object. An identifier starts with a letter A to Z or a to z or an underscore (_) followed by zero or more letters, underscores and digits (0 to 9).

    Python does not allow punctuation characters such as @, $, and % within identifiers. Python is a case sensitive programming language. Thus, *Manpower* and *manpower* are two different identifiers in Python.

