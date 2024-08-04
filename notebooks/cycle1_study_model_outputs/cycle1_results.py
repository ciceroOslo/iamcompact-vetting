"""Module that loads the result files from the 1st modelling cycle on import."""

# %%
# Imports
from pathlib import Path
import typing as tp
import pickle
import hashlib

import pyam
try:
    import openpyxl
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        'Package `openpyxl` not found. This package is required to load the '
        'result Excel files.'
    )



# %%
# Create a helper function that takes a function as an argument, and returns
# a modified function which will return the return value of the original
# function if it returns, but catch any exceptions and return them. The function
# should be properly type-annotated, with ParamSpecs to ensure that the
# modified function has the same signature and return type as the original
# function, except that it can return an exception as well as the original
# return type.
PS = tp.ParamSpec('PS')  # Parameter specifiction
RT = tp.TypeVar('RT')  # Return type
def return_exceptions(
    func: tp.Callable[PS, RT]
) -> tp.Callable[PS, RT|Exception]:
    def wrapper(*args: PS.args, **kwargs: PS.kwargs) -> RT|Exception:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return e
    return wrapper

# %%
# Define a function to open IAMC excel files with multiple sheets
def open_multisheet_iamc(path: Path|str) -> \
        pyam.IamDataFrame|Exception|dict[str, pyam.IamDataFrame|Exception]:
    sheetnames: list[str] = openpyxl.open(path).sheetnames
    if len(sheetnames) == 1:
        return return_exceptions(pyam.IamDataFrame)(path)
    else:
        return {
            sheetname: return_exceptions(pyam.IamDataFrame) \
                (path, sheet_name=sheetname)
            for sheetname in sheetnames
        }

# %%
# Get data files, and create a nested dict of IamDataFrames
# If a cached pickle file exists, load it. Otherwise, load the data files and
# save the dict as a pickle file.
try:
    data_root: Path = Path(__file__).parent
except NameError:
    data_root: Path = Path.cwd()
cache_file: Path = data_root / 'data_dict.pkl'
FORCE_RELOAD: bool = False
pickle_hash: str = '7fc3faa2781bd687cb91573dd1a81c77'
write_cache: bool = True

if cache_file.exists() and not FORCE_RELOAD:
    # First check that the md5sum hash of the pickle file matches `pickle_hash`.
    # Raise an error if not.
    print(f'Reading cache file {cache_file}, expecting MD5 hash {pickle_hash}')
    with open(cache_file, 'rb') as f:
        cache_file_content: bytes = f.read()
        cache_file_hash = hashlib.md5(cache_file_content).hexdigest()
        if cache_file_hash != pickle_hash:
            raise ValueError(
                f'Hash of pickle file {cache_file} does not match expected hash'
            )
    # Load the pickle file using the content that was already read
    data_dict: dict[str, pyam.IamDataFrame | Exception |
                    dict[str, pyam.IamDataFrame | Exception]] = pickle.loads(
        cache_file_content
    )
    print('Successfully loaded cache file.')
else:
    if not cache_file.exists():
        print(f'Cache file {cache_file} does not exist. Loading data files.')
    elif FORCE_RELOAD:
        print(f'FORCE_RELOAD is set to True. Loading data files.')
    else:
        raise RuntimeError(
            'Cache file exists, but FORCE_RELOAD is not set to True. It should '
            'not be possible to reach this point in the code in this case, '
            'please check for errors in the code.'
        )
    data_dict: dict[str, pyam.IamDataFrame | Exception |
                        dict[str, pyam.IamDataFrame | Exception]] = dict()
    _p: Path
    _idf: pyam.IamDataFrame | Exception | dict[str, pyam.IamDataFrame | Exception]
    relpaths: dict[Path, Path] = {
        _p: _p.relative_to(data_root)
        for _p in data_root.glob('**/*.xlsx')
    }
    _relpath: Path
    _abspath: Path
    for _abspath, _relpath in relpaths.items():
        _idf = open_multisheet_iamc(_abspath)
        data_dict[str(_relpath)] = _idf
    if write_cache:
        if cache_file.exists():
            raise FileExistsError(
                f'Cache file {cache_file} already exists. Please delete it '
                'before writing a new cache file, or set a different name/path '
                'in the code.'
            )
        with open(cache_file, 'wb') as f:
            pickle.dump(data_dict, f)
        # Calculate the hash of the pickle file and print it.
        with open(cache_file, 'rb') as f:
            cache_file_content = f.read()
            cache_file_hash = hashlib.md5(cache_file_content).hexdigest()
            print(
                f'Cache file written to {str(cache_file)} with MD5 hash '
                f'{cache_file_hash}'
            )

# %%
# Flatten the dict by inserting an @ sign in front of tab names for files that
# have multiple tabs
flat_data_dict: dict[str, pyam.IamDataFrame | Exception] = dict()
_pathkey: str
for _pathkey, _idf in data_dict.items():
    if isinstance(_idf, dict):
        for _tabname, _idf_tab in _idf.items():
            flat_data_dict[f'{_pathkey}@{_tabname}'] = _idf_tab
    else:
        flat_data_dict[_pathkey] = _idf

# %%
# Get only the items that are IamDataFrames
flat_data_dict_iamdfs: dict[str, pyam.IamDataFrame] = {
    _relpath: _idf for _relpath, _idf in flat_data_dict.items()
    if isinstance(_idf, pyam.IamDataFrame)
}
