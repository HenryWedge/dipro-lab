# Collaborative Token-Based Replay Protocol

This document specifies a protocol for collaborative token-based replay (TBR).
Multiple participants jointly replay events against a Petri net while keeping
activity and transition labels private.

## Roles

The protocol involves three roles:

- **Replay participants** process events assigned to them. Each participant
  locally maps activity labels to its transitions, maintains token markings for
  its places, and reports token metrics.
- **Resolver** coordinates the consumption of tokens from places. It asks the
  place owners about markings and resolves dependencies on silent transitions.
- **Aggregator** requests token metrics from replay participants and combines
  them to calculate conformance metrics.

## Privacy requirements

Activity labels and transition labels are private information. A replay
participant may know the labels of its own activities and transitions, but
must not receive labels of transitions assigned to other participants. Labels
must not be shared with the resolver or aggregator through protocol messages.
When information about a transition must be exchanged, the protocol uses
opaque identifiers that do not reveal its label.

The protocol also avoids sharing the complete Petri net with every participant.
Participants receive only the model information needed for their role. The
resolver receives place ownership and final-marking information.

## Interfaces

### Replay participant

```python
def is_place_marked(self, case_id: str, place_id: str) -> IsMarkedResult

def consume_place(self, case_id: str, place_id: str)

def fire_silent_transition(self, case_id: str, handle: str)

def get_token_metrics_for_case(self, case_id: str)
```

### Resolver

```python
def resolve_and_consume(self, case_id: str, place_id: str)

def end_trace(self, case_id: str)
```

## Protocol flow

### 1. Preparation

In an offline phase, a collaborative model is discovered, for example using the
Heuristics Miner or Inductive Miner. A trusted party assigns the model
information to the replay participants and the resolver.

Each replay participant knows only the transitions and places needed for its
role. It uses its own activity and transition labels locally. Labels of
transitions assigned to other participants are not included in its model or in
messages to other protocol participants.

The resolver knows:

- which participants own each place
- the final marking

The resolver does not need activity or transition labels.

### 2. Execution

When an event occurs, it is routed to the responsible participant without
revealing its activity label to other participants. The responsible participant
uses its local activity-to-transition mapping to identify the transition.

The participant fires the transition:

- It produces tokens in its output places and increments its produced-token
  counter.
- For each input place, it asks the resolver to resolve and consume a token
  using `resolve_and_consume(case_id, place_id)`.

The resolver asks the place owner or owners whether the place is marked using
`is_place_marked(case_id, place_id)`.

Two outcomes are possible:

1. **The place is marked, or cannot be reached through a silent transition.**
   If marked, the resolver consumes the token and the consumed-token counter
   increases. If no token is available, the missing-token counter increases.

2. **The place is not marked but may be reachable through silent transitions.**
   A silent transition may depend on places owned by other participants. The
   participant reports the required input places and an opaque handle for the
   silent transition. The resolver recursively checks those dependencies. If a
   complete path is found, it consumes the required tokens and requests that the
   responsible participant fire the silent transition. If no path is found, the
   requested place is treated as unmarked.

When a transition ends a trace, the resolver completes the trace by resolving
and consuming the places in the final marking. This accounts for tokens that
may be produced through silent transitions.

### 3. Metrics

The aggregator periodically requests
`get_token_metrics_for_case(case_id)` from the participants and aggregates the
produced, consumed, missing, and remaining token counts.
