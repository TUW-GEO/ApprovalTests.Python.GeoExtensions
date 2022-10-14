from typing import Dict, Tuple, Callable

from approvaltests import Options, ScenarioNamer
from approvaltests.namer import NamerBase

from pytest_approvaltests_geo.scrubbers import TagsScrubber


class GeoOptions(Options):
    _TAGS_SCRUBBER_FUNC = "tags_scrubber_func"
    _NAMER_WRAPPER_SCENARIO_BY_TAGS = "NamerWrapperScenarioByTags"

    def scrub_tags(self, data: Dict):
        if self.has_tags_scrubber():
            return self.fields[GeoOptions._TAGS_SCRUBBER_FUNC](data)
        return data

    def with_tags_scrubber(self, scrubber_func: TagsScrubber) -> "GeoOptions":
        return GeoOptions({**self.fields, **{GeoOptions._TAGS_SCRUBBER_FUNC: scrubber_func}})

    def has_tags_scrubber(self):
        return GeoOptions._TAGS_SCRUBBER_FUNC in self.fields

    def with_scenario_by_tags(self, tags_to_names: Callable[[Dict], Tuple[str, ...]]):
        return GeoOptions({**self.fields, **{GeoOptions._NAMER_WRAPPER_SCENARIO_BY_TAGS: tags_to_names}})

    def has_scenario_by_tags(self):
        return GeoOptions._NAMER_WRAPPER_SCENARIO_BY_TAGS in self.fields

    def wrap_namer_in_tags_scenario(self, namer: NamerBase, tags: Dict):
        if self.has_scenario_by_tags():
            return ScenarioNamer(namer, *self.fields[GeoOptions._NAMER_WRAPPER_SCENARIO_BY_TAGS](tags))
