# NASA tutorial excerpt (not a training dataset)

`firms_nasa_tutorial.csv` transcribes only the first five observations of the
worldwide VIIRS NOAA-20 output table in NASA's [FIRMS API tutorial](https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html), consulted 2026-09-06.

Observed date/time: 2025-06-06 00:01 UTC. The tutorial renders HHMM as integer `1`;
this CSV restores it to `0001`. All other values are copied as published. These
are African coordinates, **not an India dataset**, and not a fresh API download.
NASA's tutorial is the source; independent archive retrieval was not performed.
No labels, facility context, imagery validation or continuous history are supplied.
The excerpt tests real published FIRMS formatting and event construction only.
The command hashes the exact source CSV and preserves an unchanged raw copy.

Default 1 km / 24 hour clustering yields three candidate events (2, 1, 2 detections).
A zero historical count means no earlier rows in this excerpt, not absence of
past thermal activity. Do not use this tiny, selected excerpt to train or evaluate.
