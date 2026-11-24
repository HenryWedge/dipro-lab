# DiPro Lab

DiPro Lab is a test lab for developing and evaluating distributed process
mining algorithms. It contains experimental algorithm implementations,
supporting runtime components, and tools for generating distributed event data.

## Repository structure

- `algorithms/` — experimental process mining algorithms, including conformance
  checking and anomaly detection
- `dpm-bench/` — runtime support for distributed algorithms
- `def/` — Distributed Event Factory submodule for generating distributed event
  streams

## Algorithms and protocols

- [Collaborative Token-Based Replay (TBR)](algorithms/conformance/tbr/tbr_algorithm.md)
