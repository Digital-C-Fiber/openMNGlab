# OpenMNGLab Quickstart

## Installation

To install openmnglab, download the whl-file and install with pip in an environment (like conda) of your choosing.

## Basics

OpenMNGLab follows a structure, which combines object orientation with contract based programming: Functions produce and consume data. Those functions and the dataflow are mapped in an execution plan. That execution plan can then be executed by passing it to an executor. The data produced by the functions can then be retrieved. Data between functions is encapsulated in data containers which may implement additional meta-functions.

### Run-along example

Please see `quickstart.ipynb` for an interactive example of how to use OpenMNGLab

## Existing functionalities

### Data Loading

#### Dapsys

**parameters**:

* file: Path to the DAPSYS file

* stim_folder: The stimulator folder inside the DAPSYS file (i.e. "NI Pulse Stimulator")

* main_pulse: Name of the main pulse, defaults to "Main Pulse"

* continuous_recording: Name of the continuous recording, defaults to "Continuous Recording"

* responses: Name of the folder containing the responses, defaults to "responses"

* tracks: Define which tracks to load from the file. Tracks must be present in the "Tracks for all Responses" folder. "all" loads all tracks found in that subfolder.

##### Output

* **Continuous Recording**: continuous recording from the file. timestamps as float index, signal values as float  
  values pd.Series[[TIMESTAMP: float], float].  
* **Stimuli list**: list of stimuli timestamps. Indexed by the global stimulus id  
  (the stimulus id amongst all stimuli in the file), the label of stimulus and the id of the stimulus type / label  
  (the id amongst all other stimuli in the file which have the same label):  
  pd.Series[[GLOBAL_STIM_ID: int, STIM_TYPE: str, STIM_TYPE_ID: int], float]  
* **tracks**: List of all sorted tracks. Indexed by the global stimulus id they are attributed to, the name of the track and their id respective to the track.  
  pd.Series[[GLOBAL_STIM_ID: int, TRACK: str, TRACK_SPIKE_IDX: int], float]

### Processing

#### Windowing

Takes a set of values and transforms them based on a fixed window.  

**In**: series of numbers  

**Out**: Series of pd.Interval, with the same index as the input series.

**parameters**:

* **offset_low**: quantity of low offset

* **offset_high**: quantity of high offset

* **name**: name of the returned series

* **closed**: how the interval is closed / open

#### Interval Data

Extracts the data of intervals from a continuous series. Can also calculate the derivative (or diff) in one go. Can normalize timestamps based on their beginning.

**In**: [Intervals, Continuous Series]  

**Out**: Dataframe with the Interval inputs index concatenated with the index of the continuous series or the respective normalized timestamps. Columns are based on the `first_level` and `levels` parameter.

**parameters**:

* **first_level**: first level (diff or derivative) to include in the output data frame

* **levels**: additional levels to include in the output data frame

* **derivative_base**: quantity to base the time of the derivative on. If None, will calculate the diffs

* **interval**: The sampling interval of the signal. If this is not given, the interval will be approximated by calculating the diff of the first two samples.

* **use_time_offsets**: if True, will use the offset the index timestamps to the start of each interval. defaults to True. USE ONLY WITH REGULARLY SAMPLED SGINALS!

#### waveform components

Calculates the components of waveforms.  

**In**: Interval data with level 0 and 1.  

**Out**: Dataframe with the waveform components, columns are named based on PRINCIPLE_COMPONENTS constant. Index is taken from the input series non-timestamp multiindex.

**params**: None

#### SPDF Features

Calculates the SPDF features of waveforms based on their components and waveforms.  

**In**: [WaveformComponents, IntervalData with levels 0,1,2] WaveformComponents and IntervalData must have the same base multiindex  

**Out**: Dataframe with the features, indexed by the same index as the WaveformComponents input. F4 will always be nan.

**params**: None

### Figures

#### Waveforms

Function to plot waveforms. Can either plot average waveforms or each for its own.  
Multi-plots can be created by using the col and row parameters which are passed to the underlying seaborn function.  

**In**: IntervalData with normalized timestamps  

**Out**: figure based on the configuration

**params**:

* **mode**: "average" prints the average of the waveforms and their standard deviation, "individual" plots all waveforms individually

* **selector**: function to filter the incoming dataframe (e.g. plotting only a subset of waveforms):param column: column of the signal

* **fig_args**: additional arguments to pass to plt.figure(). Only active when col and row are both None

* **alpha**: Alpha channel for the lines. Only active when mode is individual. Smaller values will make each individual line more transparent

* **row**: index or column to create supblot rows:param theme: custom theme passed to seaborn

* **col**: index or column name to create subplot columns

* **color_dict**: dictionary mapping from track names to mpl-compatible color definitions

* **time_col**: index or column for the timestamps

* **stim_idx**: index to differentiate individual stimuli by

* **sns_args**: additional arguments passed to seaborn

## Implement own functionalities

Functions are split into two parts: A function definition class, which acts as a factory method for the actual function class implementing the function interface. The function definition specifies the input and output dataschemes and is used for the planning. Executors use the function definition to instantiate function objects which do the actual computations.

### 1. Function implementation

When implementing your own functions, you should first start with the function implementation.

For this example, we will implement a function which takes two series and either returns the first or the second one based on a static parameter.



Declare a new class and derive it from `FunctionBase`, which is the base class implementing the `IFunction` interface:

```python
from typing import Optional, Iterable

from openmnglab.functions.base import FunctionBase
from openmnglab.model.datamodel.interface import IDataContainer


class SeriesChooserFunc(FunctionBase):
    def execute(self) -> Iterable[IDataContainer]:
        pass

    def set_input(self, *data_in: IDataContainer):
        pass
```

The `IFunction` interface specifies, that a function class must provide the `set_input` method to set the input data containers and an `execute` method which will execute the function and return its outputs. Per contract, you may assume that `execute` is only called after `set_input` .

The function should take two inputs in the form of a `PandasContainer` and returns a single `PandasContainer`. We will create the constructor and concretise the type annotations of our class:

```python
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
```

Now implement the (trivial) execution function. For the sake of demonstration, we will not simple return the chosen container, but will construct a new one with the chosen series. Remember that a `PandasContainer` requires a dictionary which contains the unit of each column and index of the contained pandas structure.

```python
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
```

### 2. Implement the function definition

Now it is time to implement the function definition.

Again, there is some boilerplate code:

```python
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
```

First thing to do is to choose a unique identifier for our function and initialize the super constructor with it, i.e. `"openmgnlab.qs.serieschooser"`. For your own function, you could always use something like your name in the identifier to decrease the chance of a collision.

We will have to specify the `config_hash`. This property is used to calculate a hash unique for the function configuration, so calculated data can be uniquely identified later. Add our sole config argument to the constructor and return the hash of it. You can use `openmnglab.util.hashing.Hash` for an easy, fluent and typed wrapper around Pythons hashing functions. Using that class will also ensure, that all hashes are calculated the same way.

```python
def __init__(self, chosen_series: int):
    super().__init__('openmgnlab.qs.serieschooser')
    self.chosen_series = chosen_series

@property
def config_hash(self) -> bytes:
    return Hash().int(self.chosen_series).digest()
```

In the next step, we will define the dataschemas our function will consume and produce. As we do not have specific requirements, we can just return a new `PandasInputDataScheme` with an empty `SeriesSchema`, to just accept any series whatsoever.

```python
@property
def consumes(self) -> tuple[PandasInputDataScheme[SeriesSchema],PandasInputDataScheme[SeriesSchema]]:
    return PandasInputDataScheme(SeriesSchema()),PandasInputDataScheme(SeriesSchema())
```

we will also have to implement a function that will return the data schema for a concrete set of inputs. In our case, we can predict the concrete schema of the returned series based on our `chosen_series` parameter:

```python
def production_for(self, schema_a: PandasOutputDataScheme[SeriesSchema], schema_b: PandasOutputDataScheme[SeriesSchema]) -> tuple[PandasOutputDataScheme[SeriesSchema]]:
    return schema_a if self.chosen_series == 0 else schema_b,
```

Finally, we have to implement the factory function :

```python
def new_function(self) -> SeriesChooserFunc:
    return SeriesChooserFunc(self.chosen_series)
```

The complete implementation should now look something like this:

```python
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

```

You can now go ahead and use `SeriesChooser` in any analysis flow.
