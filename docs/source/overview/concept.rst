Concept
=======

oMNGl is implemented around the concept of an execution flow; functions and dataflow between them is defined beforehand
in an execution plan. Only when the plan is executed, the concrete outputs of the functions are created.
This concept is realized following a relatively strict `object orientation <https://en.wikipedia.org/wiki/Object-oriented_programming>`_
with elements of `contract programming <https://en.wikipedia.org/wiki/Design_by_contract>`_.

This means, that the "model" of oMNGl (i.e. what kind of abstract things there are and how they interact) are defined by interfaces.
Of course, Python does not have the concept of an "interface" and only knows abstract classes.
But that is enough to mimic an interface and, by convention, an interface in oMNGl is defined
as an abstract class that only contains abstract methods and properties and its name should start with a capital ``I`` to differentiate
it from classes (i.e. ``ÌInterface``). How the model looks in detail is described here.

.. _dataconcept:
Data exchange
--------------
The pandas library serves as the primary way for functions to exchange data. Pandas series or data frames are wrapped in a container structure
which requires that all elements of the structure (indices, columns / series) are named and also carries a dictionary, where each element of the pandas structure
must be mapped to the correlating quantity using `python-quantities <https://github.com/python-quantities/python-quantities>`_. This defines data
unambiguously in a human-readable way.

Functions
----------
Functions are split into two parts: The function definition (defined by :class:`~openmnglab.model.functions.interface.IFunctionDefinition`) is used in the execution plan and serves as a factory method for the actual function implementation (defined by :class:`~openmnglab.model.functions.interface.IFunction`).
Function definitions  provide the number of in- and outputs of the function, as well as a data schema for each in and output. This serves to main goals:
First of all, the schema can be used to validate the dataflow while building the execution plan. Secondly, it forces function implementations to reason about their in- and output behaviour.
A function that fails on a validated input or produces an output that does not match the promised schema is considered faulty.
Function definitions also provide a hash value unique to the function and its configuration, which is used by planner and executors to identify unique instances and data.

Planning
--------
Planners accept instances of function definitions and return a number of data proxies, one for each of the expected outputs of the function definition.
These proxies can be used to further plan the execution by passing them as inputs of other functions.

Execution
---------
Execution is as simple as passing an execution plan to an executor and calling :meth:`~openmnglab.model.execution.interface.IExecutor.execute`.
Once the execution finishes, data can be retrieved by its hash via :attr:`~openmnglab.model.execution.interface.IExecutor.data` or by passing the proxydata object to
:meth:`~openmnglab.model.execution.interface.IExecutor.get`.

