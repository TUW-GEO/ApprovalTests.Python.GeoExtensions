from typing import Callable, Dict, Union, List, Tuple, get_args, Any, Sequence

import numpy as np
from approvaltests.scrubbers.scrubbers import Scrubber, create_regex_scrubber, combine_scrubbers, scrub_all_dates, \
    scrub_all_guids

JsonLikeCollection = Union[Dict, List, Tuple]
RecursiveScrubber = Callable[[JsonLikeCollection], JsonLikeCollection]
SequenceScrubber = Callable[[Sequence], Sequence]


def scrub_recursive(tags: JsonLikeCollection, scrubber: Scrubber) -> JsonLikeCollection:
    if isinstance(tags, Dict):
        return scrub_dict_recursive(tags, scrubber)
    if isinstance(tags, List):
        return scrub_list_recursive(tags, scrubber)
    if isinstance(tags, Tuple):
        return scrub_tuple_recursive(tags, scrubber)


def scrub_dict_recursive(tags: Dict, scrubber: Scrubber) -> Dict:
    scrubbed = {}
    for k, v in tags.items():
        if isinstance(k, str):
            k = scrubber(k)
        v = scrub_element(v, scrubber)
        scrubbed[k] = v
    return scrubbed


def scrub_element(element: Any, scrubber: Scrubber) -> Any:
    if isinstance(element, str):
        element = scrubber(element)
    if isinstance(element, get_args(JsonLikeCollection)):
        element = scrub_recursive(element, scrubber)
    return element


def scrub_list_recursive(tags: List, scrubber: Scrubber) -> List:
    return [scrub_element(t, scrubber) for t in tags]


def scrub_tuple_recursive(tags: Tuple, scrubber: Scrubber) -> Tuple:
    return tuple(scrub_element(t, scrubber) for t in tags)


def scrub_sequential(elems: Sequence, scrubber: Scrubber) -> Sequence:
    return [scrubber(e) for e in elems]


def make_scrubber_recurse(scrubber: Scrubber) -> RecursiveScrubber:
    return lambda elems: scrub_recursive(elems, scrubber)


def make_scrubber_sequential(scrubber: Scrubber) -> SequenceScrubber:
    return lambda elems: scrub_sequential(elems, scrubber)


def identity_recursive_scrubber(tags: Dict) -> Dict:
    return tags


def identity_sequence_scrubber(v: Sequence) -> Sequence:
    return v


def scrub_xarray_metadata(a, tags_scrubber):
    a.attrs = tags_scrubber(a.attrs)
    for name in a.coords:
        a[name].attrs = tags_scrubber(a[name].attrs)
    for name in getattr(a, 'data_vars', {}):
        a[name].attrs = tags_scrubber(a[name].attrs)

    return a


def scrub_xarray_coordinates(a, coords_scrubber):
    for coord in a.coords:
        cv = a[coord]
        if cv.dtype.type is np.str_:
            a = a.assign_coords({coord: (cv.dims[0], coords_scrubber(cv.values))})
    return a


def scrub_all_yeoda_dates(data: str) -> str:
    return create_regex_scrubber(
        r"\d{4}\d{2}\d{2}T\d{2}\d{2}\d{2}",
        lambda t: f"<yeoda_date{t}>",
    )(data)


def scrub_all_short_commits(data: str) -> str:
    return create_regex_scrubber(
        r"[0-9a-fA-F]{7}",
        lambda t: f"<short_commit_{t}>",
    )(data)


def scrub_all_tags(data: str) -> str:
    return create_regex_scrubber(
        r"v\d\.\d\.\d",
        lambda t: f"<tag_{t}>",
    )(data)


def scrub_yeoda_datacube_metadata(data: str) -> str:
    return combine_scrubbers(
        scrub_all_dates,
        scrub_all_yeoda_dates,
        scrub_all_guids,
        scrub_all_short_commits,
        scrub_all_tags,
    )(data)
