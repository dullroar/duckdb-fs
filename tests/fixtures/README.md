# GX fixture provenance

`demo_weather_output/` is an immutable copy of the twelve extractor CSVs from
`metadata_driven_gx/environments/demo_weather/output/` at commit
`633f3cf651ec0384fe9a93574b1e82ffc06e4266`.

It contains six summary files (50 expectation rows: 21 pass, 29 fail) and six detail
files (34 exploded failure-evidence rows). The fixture is intentionally owned by this
repository so its tests do not depend on a sibling checkout or on Great Expectations.
