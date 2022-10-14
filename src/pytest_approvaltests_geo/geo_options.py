from typing import Dict

from approvaltests import Options

from pytest_approvaltests_geo.scrubbers import TagsScrubber


class GeoOptions(Options):
    _TAGS_SCRUBBER_FUNC = "tags_scrubber_func"

    def scrub_tags(self, data: Dict):
        if self.has_tags_scrubber():
            return self.fields[GeoOptions._TAGS_SCRUBBER_FUNC](data)
        return data

    def with_tags_scrubber(self, scrubber_func: TagsScrubber) -> "GeoOptions":
        return GeoOptions({**self.fields, **{GeoOptions._TAGS_SCRUBBER_FUNC: scrubber_func}})

    def has_tags_scrubber(self):
        return GeoOptions._TAGS_SCRUBBER_FUNC in self.fields
