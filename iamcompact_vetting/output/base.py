"""Base classes and abstract base classes for creating and writing output.

Classes
-------
ResultOutput
    Abstract base class for creating output from results. Is intended to be take
    results from one instance or a collection of instances of either
    `pathways_ensemble_analysis.Criterion` (including
    `iamcompact_vetting.criteria.TimeseriesRefCriterion`) or
    `iamcompact_vetting.targets.CriterionTargetRange` subclasses. Different
    subclasses will implement output for different types and collections of
    these classes. The subclasses should generally implement the
    `prepare_output` method to return a nominally format-independent output data
    structure, and use a `ResultsWriter` subclass instance to write the output
    to a desired format, through the `write` method.
ResultsWriter
    Abstract base class for writing output. Subclasses should implement writing
    to different formats. In most cases, each non-abstract subclass will be
    intended for use with a specific subclass of `ResultOutput` (which in turn
    is designed to be used with a specific instance or collection of instances
    of `pathways_ensemble_analysis.Criterion` or
    `iamcompact_vetting.targets.CriterionTargetRange` subclasses).
"""
import typing as tp
from abc import ABC, abstractmethod



CritTypeVar = tp.TypeVar('CritTypeVar')
"""TypeVar for the type of `Criterion` or `CriterionTargetRange` expected by a
`ResultOutput` subclass."""
OutputDataTypeVar = tp.TypeVar('OutputDataTypeVar')
"""TypeVar for the type of data to be output by a `ResultOutput` subclass
through its `prepare_output` method, and to be written by a `ResultsWriter`
through its `write` method."""
WriteReturnTypeVar = tp.TypeVar('WriteReturnTypeVar')
"""TypeVar for the datatype to be returned by the `write` method of a
`ResultsWriter` subclass."""


class ResultsWriter(ABC, tp.Generic[OutputDataTypeVar, WriteReturnTypeVar]):
    @abstractmethod
    def write(self, output_data: OutputDataTypeVar) -> WriteReturnTypeVar:
        """Write the output data to a desired format.

        Parameters
        ----------
        output_data : OutputDataTypeVar
            The data to be written, prepared into the proper data type by a
            `ResultOutput` subclass instance.

        Returns
        -------
        WriteReturnTypeVar
            Appropriate return value for the `write` method defined by a
            subclass. Can be `None` if no return value is desired.
        """
        ...
#END abstract class ResultsWriter

WriterTypeVar = tp.TypeVar('WriterTypeVar', bound=ResultsWriter, covariant=True)
"""TypeVar for the type of `ResultsWriter` subclass to be used by a
`ResultOutput` subclass instance."""



class ResultOutput(
        ABC,
        tp.Generic[CritTypeVar, OutputDataTypeVar, WriteReturnTypeVar]
):
    """Abstract base class for creating output from results.

    Is intended to be take results from one instance or a collection of
    instances of either `pathways_ensemble_analysis.Criterion` (including
    `iamcompact_vetting.criteria.TimeseriesRefCriterion`) or
    `iamcompact_vetting.targets.CriterionTargetRange` subclasses. Different
    subclasses will implement output for different types and collections of
    these classes. The subclasses should generally implement the
    `prepare_output` method to return a nominally format-independent output
    data structure, and use a `ResultsWriter` subclass instance to write the
    output to a desired format, through the `write` method.
    """

    def __init__(
            self,
            writer: ResultsWriter[OutputDataTypeVar, WriteReturnTypeVar],
    ) -> None:
        """
        Parameters
        ----------
        writer : WriterTypeVar
            The writer to be used to write the output.
        """
        self.writer: ResultsWriter[OutputDataTypeVar, WriteReturnTypeVar] = \
            writer
    ###END def ResultOutput.__init__

    @abstractmethod
    def prepare_output(
            self,
            results: CritTypeVar,
            /,
            **kwargs
    ) -> OutputDataTypeVar:
        """Prepare the output data for writing.

        Parameters
        ----------
        results : CritTypeVar
            The results to be written, prepared into the proper data type by a
            `ResultOutput` subclass instance.

        Returns
        -------
        OutputDataTypeVar
            The data to be written, prepared into the proper data type by a
            `ResultOutput` subclass instance.
        """
        ...
    ###END def ResultOutput.prepare_output

    def write_output(
            self,
            output: OutputDataTypeVar,
            /,
            writer: tp.Optional[ResultsWriter[OutputDataTypeVar, WriteReturnTypeVar]] \
                = None,
            **kwargs
    ) -> WriteReturnTypeVar:
        """Write the output data to the format written by `writer`.

        This method is used for result outputs that have already been prepared
        into the proper format, usually by `self.prepare_output`. To write
        outputs directly based on `Criterion` or `CriterionTargetRange`
        instances, use `self.write_rsults` instead.

        Parameters
        ----------
        output : OutputDataTypeVar
            The data to be written, prepared into the proper output data
            structure, usually through `self.prepare_output`.
        writer : tp.Optional[WriterTypeVar]
            The writer to be used to write the output. If `None`, the
            `self.writer` attribute is used.
        **kwargs
            Additional keyword arguments to be passed to `writer.write`.

        Returns
        -------
        WriteReturnTypeVar
            The return value from the `writer.write` method.
        """
        if writer is None:
            writer = self.writer
        return writer.write(output, **kwargs)
    ###END def ResultOutput.write_output

    def write_results(
            self,
            results: CritTypeVar,
            /,
            writer: tp.Optional[ResultsWriter[OutputDataTypeVar, WriteReturnTypeVar]] \
                = None,
            **kwargs
    ) -> WriteReturnTypeVar:
        """Write the results to the format written by `writer`.

        Parameters
        ----------
        results : CritTypeVar
            The results to be prepared into the proper data structure through
            `self.prepare_output`, which is then written through
            `self.write_output`, using the `writer` parameter.
        writer : tp.Optional[WriterTypeVar]
            The writer to be used to write the output. If `None`, the
            `self.writer` attribute is used.
        **kwargs
            Additional keyword arguments to be passed to `writer.write`.

        Returns
        -------
        WriteReturnTypeVar
            The return value from the `writer.write` method.
        """
        output: OutputDataTypeVar = self.prepare_output(results, **kwargs)
        return self.write_output(output, writer, **kwargs)
    ###END def ResultOutput.write_results

###END abstract class ResultOutput
