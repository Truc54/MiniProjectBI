# Staging tables

Create one source-aligned table per selected CSV in schema stg. Keep source keys and columns traceable to the CSV. Convert the literal source sentinel \N to SQL NULL; do not replace missing values with zero.

Recommended Phase 1 core tables:

- stg.races
- stg.results
- stg.drivers
- stg.constructors
- stg.circuits
- stg.status
- stg.seasons

Add qualifying.csv only if the project scope needs its session times. The results table already contains grid, which supports the core start-position analysis.
