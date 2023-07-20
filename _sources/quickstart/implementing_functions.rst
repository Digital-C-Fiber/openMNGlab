Implementing a function
=======================

Functions are split into two parts:
A function definition class, which acts as a factory method for the actual function class implementing the function interface.
The function definition specifies the input and output dataschemes and is used for the planning.
Executors use the function definition to instantiate function objects which do the actual computations.

Implementing the function
--------------------------
When implementing your own functions, you should first start with the function implementation.

For this example, we will implement a function which takes two series and either returns the first or the second one based on a static parameter.

Boilerplate
^^^^^^^^^^^
Declare a new class and derive it from :class:`~openmnglab.functions.base.FunctionBase`, which is the base class implementing the :class:`~openmnglab.model.functions.interface.IFunction` interface.

.. code-block:: python

    from typing import Optional, Iterable

    from openmnglab.functions.base import FunctionBase
    from openmnglab.model.datamodel.interface import IDataContainer


    class SeriesChooserFunc(FunctionBase):
        def execute(self) -> Iterable[IDataContainer]:
            pass

        def set_input(self, *data_in: IDataContainer):
            pass

You function implementation must provide the methods ``set_input`` and ``execute``. ``set_input`` sets the input data of the function and with a call to
``execute``, the function should execute on the previously set data.

Implementation
^^^^^^^^^^^^^^
.. note::
    The contracts defined by the model between an executor and a function
    give you some guarantees when implementing the function:

    * ``execute`` may only be called after a successfull call to ``set_input``
    * All data passed to ``set_input`` must adhere to the dataformat specified by the function definition

    If your function fails because of one of those guarantees were ignored by the executor implementation, that is not your problem.

While the execution framework can -in theory- handle all types data, the main way to pass data between functions is by using pandas data structures, wrapped in a
:class:`~openmnglab.datamodel.pandas.model.PandasContainer`. You must always name all elements (indizes, columns, series) and provide a quantity for each element. Please see :ref:`dataconcept` for a reasoning behind this

The function should take two inputs and return a single one `PandasContainer`.
We will implement the constructor and specify the type annotations of our class:

.. code-block:: python

    from typing import Optional, Iterable

    import pandas as pd

    from openmnglab.datamodel.pandas.model import PandasContainer
    from openmnglab.functions.base import FunctionBase
    from openmnglab.model.datamodel.interface import IDataContainer


    class SeriesChooserFunc(FunctionBase):
        def __init__(self, chosen_series: int):
            # annotate with PandasContainer type. No optional required, as it should always be initialized when a read-access occours.
            self.series_a_container: PandasContainer[pd.Series] = None
            self.series_b_container: PandasContainer[pd.Series] = None
            self.chosen_series = chosen_series

        def execute(self) -> tuple[PandasContainer[pd.Series]]:
            pass

        def set_input(self, series_a_container: PandasContainer[pd.Series], series_b_container: PandasContainer[pd.Series]):
            self.series_a_container = series_a_container
            self.series_b_container = series_b_container

Now implement the (trivial) execution function. For the sake of demonstration, we will not simple return the chosen container, but will construct a new one with the chosen series.
Remember that a `PandasContainer` requires a dictionary which contains the unit of each column and index of the contained pandas structure.

.. important::
    Always make sure to include a comma at the end of ``execute`` to return a tuple! Returning a single item not wrapped in a tuple is not supported at this time.

.. code-block:: python
    :emphasize-lines: 17, 18

    import pandas as pd

    from openmnglab.datamodel.pandas.model import PandasContainer
    from openmnglab.functions.base import FunctionBase


    class SeriesChooserFunc(FunctionBase):
        def __init__(self, chosen_series: int):
            # annotate with PandasContainer type. No optional required, as it should always be initialized when a read-access occours.
            self.series_a_container: PandasContainer[pd.Series] = None
            self.series_b_container: PandasContainer[pd.Series] = None
            self.chosen_series = chosen_series

        def execute(self) -> tuple[PandasContainer[pd.Series]]:
            chosen_container = self.series_a_container if self.chosen_series == 0 else self.series_b_container
            return_container = PandasContainer(chosen_container.data, chosen_container.units)
            # remember to return a tuple
            return return_container,

        def set_input(self, series_a_container: PandasContainer[pd.Series], series_b_container: PandasContainer[pd.Series]):
            self.series_a_container = series_a_container
            self.series_b_container = series_b_container

Test
^^^^^
You should now test your function to make sure it works like intended:

.. important::::
    Always make sure to include a comma to unpack the result of ``execute``.

.. code-block:: python
    :emphasize-lines: 19, 20

    import quantities as pq

    # construct the series and name them (and their index)
    ser_a = pd.Series([1,2,3], name="Series A")
    ser_b = pd.Series([4,5,6], name="Series B")
    for s in (ser_a,ser_b):
        s.index.name = "number idx"

    # put both series in a container, make the series themself and its index dimensionless
    dimless_container = lambda s: PandasContainer(s, units={s.name:pq.dimensionless, s.index.name:pq.dimensionless})
    ser_a_container = dimless_container(ser_a)
    ser_b_container = dimless_container(ser_b)

    # construct an  instance of the function, select the second series
    chooser = SeriesChooserFunc(1)
    # set the input
    chooser.set_input(ser_a_container, ser_b_container)
    # execute it; remember to include the comma to unpack the returned tuple
    chosen_series_container, = chooser.execute()

    print(chosen_series_container)



Implementing the function definition
-------------------------------------

Right now, our function is working, but cannot be used in the execution framework. To use it in an execution flow, we need to implement a function definition.
Function definitions are defined in :class:`~openmnglab.model.functions.interface.IFunctionDefinition`. Function definitions provide data schemas to verify that only compatible
in- and outputs are connected during planning. They also must provide a hash value which uniquely identifies the function and its configuration. That hash must be the same for all
instances of the function which are running the same configuration.

Boilerplate
^^^^^^^^^^^
We will derive our implementation from the base class :class:`~openmnglab.functions.base.FunctionDefinitionBase`,
which implements some default behaviours to reduce the required amount of boilerplate.

.. code-block:: python

    class SeriesChooser(FunctionDefinitionBase):
        def __init__(self):
            super().__init__('')

        @property
        def config_hash(self) -> bytes:
            return super().config_hash

        @property
        def consumes(self) -> Optional[Sequence[IInputDataScheme] | IInputDataScheme]:
            pass

        def production_for(self, *inputs: IInputDataScheme) -> Optional[Sequence[IOutputDataScheme] | IOutputDataScheme]:
            pass

        def new_function(self) -> IFunction:
            pass

Implementation
^^^^^^^^^^^^^^
Function identification
"""""""""""""""""""""""
First thing to do is to choose a unique identifier for our function and initialize the super constructor with it, i.e. `openmgnlab.qs.serieschooser`.

.. note::
    For your own functions include something like your git username in the identifier to decrease the chance of a collision.

.. code-block:: python

    def __init__(self):
        super().__init__('openmgnlab.qs.serieschooser')

Config hash
"""""""""""

We will have to specify the :attr:`~openmnglab.model.functions.interface.IFunctionDefinition.config_hash`. This property is used to calculate a hash unique for the configuration of the function, so calculated data can be uniquely identified later.
Add our sole config argument to the constructor and return the hash of it. You should use :class:`openmnglab.util.hashing.Hash` for an easy, fluent and typed wrapper around Pythons hashing functions.

.. note::
    :class:`~openmnglab.functions.base.FunctionDefinitionBase` implements :attr:`~openmnglab.model.functions.interface.IFunctionDefinition.identifying_hash`
    by combining the hash of the function id with the result of :attr:`~openmnglab.model.functions.interface.IFunctionDefinition.config_hash`.

.. note::
    Data ids is calculated by combining the result of :attr:`~openmnglab.model.functions.interface.IFunctionDefinition.identifying_hash` with the number of the output and
    the ids of the input data (if any). This allows unique identification of data throughout the execution.

.. code-block:: python

    @property
    def config_hash(self) -> bytes:
        return Hash().int(self.chosen_series).digest()

Data schemas
""""""""""""
In the next step, we will define the dataschemas our function will consume and produce. As we do not have specific requirements, we can just return a new `PandasInputDataScheme` with an empty `SeriesSchema`, to just accept any series whatsoever.

.. code-block:: python

    @property
    def consumes(self) -> tuple[PandasInputDataScheme[SeriesSchema],PandasInputDataScheme[SeriesSchema]]:
        return PandasInputDataScheme(SeriesSchema()),PandasInputDataScheme(SeriesSchema())


we will also have to implement a function that will return the data schema for a concrete set of inputs. In our case, we can predict the concrete schema of the returned series based on our `chosen_series` parameter:

.. code-block:: python

    def production_for(self, schema_a: PandasOutputDataScheme[SeriesSchema], schema_b: PandasOutputDataScheme[SeriesSchema]) -> tuple[PandasOutputDataScheme[SeriesSchema]]:
        return schema_a if self.chosen_series == 0 else schema_b,


Finally, we have to implement the factory function

.. code-block:: python

    def new_function(self) -> SeriesChooserFunc:
        return SeriesChooserFunc(self.chosen_series)

Complete implementation
-----------------------
.. code-block:: python

    import pandas as pd
    from pandera import SeriesSchema

    from openmnglab.datamodel.pandas.model import PandasContainer, PandasOutputDataScheme, \
        PandasInputDataScheme
    from openmnglab.functions.base import FunctionBase, FunctionDefinitionBase
    from openmnglab.util.hashing import Hash


    class SeriesChooserFunc(FunctionBase):
        def __init__(self, chosen_series: int):
            # annotate with PandasContainer type. No optional required, as it should always be initialized when a read-access occours.
            self.series_a_container: PandasContainer[pd.Series] = None
            self.series_b_container: PandasContainer[pd.Series] = None
            self.chosen_series = chosen_series

        def execute(self) -> tuple[PandasContainer[pd.Series]]:
            chosen_container = self.series_a_container if self.chosen_series == 0 else self.series_b_container
            return_container = PandasContainer(chosen_container.data, chosen_container.units)
            # remember to return a tuple
            return return_container,

        def set_input(self, series_a_container: PandasContainer[pd.Series], series_b_container: PandasContainer[pd.Series]):
            self.series_a_container = series_a_container
            self.series_b_container = series_b_container


    class SeriesChooser(FunctionDefinitionBase):
        def __init__(self, chosen_series: int):
            super().__init__('openmgnlab.qs.serieschooser')
            self.chosen_series = chosen_series

        @property
        def config_hash(self) -> bytes:
            return Hash().int(self.chosen_series).digest()

        @property
        def consumes(self) -> tuple[PandasInputDataScheme[SeriesSchema], PandasInputDataScheme[SeriesSchema]]:
            return PandasInputDataScheme(SeriesSchema()), PandasInputDataScheme(SeriesSchema())

        def production_for(self, schema_a: PandasOutputDataScheme[SeriesSchema],
                           schema_b: PandasOutputDataScheme[SeriesSchema]) -> tuple[PandasOutputDataScheme[SeriesSchema]]:
            return schema_a if self.chosen_series == 0 else schema_b,

        def new_function(self) -> SeriesChooserFunc:
            return SeriesChooserFunc(self.chosen_series)
