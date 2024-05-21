"""Module for definitin dimension (column) names for IAM datasets."""
import enum



class IamDim(str, enum.Enum):
    """Dimension (column) names used by `pyam.IamDataFrame` objects."""
    MODEL = 'model'
    SCENARIO = 'scenario'
    REGION = 'region'
    VARIABLE = 'variable'
    UNIT = 'unit'
    TIME = 'year'
###END class IamDim
