from typing import Callable, Dict, Union, List, Tuple, get_args, Any

from approvaltests.scrubbers.scrubbers import Scrubber

JsonLikeCollection = Union[Dict, List, Tuple]
RecursiveScrubber = Callable[[JsonLikeCollection], JsonLikeCollection]


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


def make_scrubber_recurse(scrubber: Scrubber) -> RecursiveScrubber:
    return lambda elems: scrub_recursive(elems, scrubber)


def identity_recursive_scrubber(tags: Dict) -> Dict:
    return tags


def scrub_xarray_data(a, scrubber):
    a.attrs = scrubber(a.attrs)
    for name in a.coords:
        a[name].attrs = scrubber(a[name].attrs)
    for name in getattr(a, 'data_vars', {}):
        a[name].attrs = scrubber(a[name].attrs)

    return a
