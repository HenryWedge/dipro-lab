from process_mining.domain.event import Event


class EventLog:
    def __init__(self, traces=None):
        if traces:
            self.traces = traces
        else:
            self.traces = {}

    def add_event(self, event: Event):
        if event.case_id not in self.traces:
            self.traces[event.case_id] = []
        self.traces[event.case_id].append(event)

    def add_events(self, events):
        for event in events:
            self.add_event(event)

    def filter_case_ids(self, case_ids):
            selected_case_ids = set(case_ids)
            new_event_log = EventLog()
            for case_id in self.traces:
                if case_id in selected_case_ids:
                    for event in self.traces[case_id]:
                        new_event_log.add_event(event)
            return new_event_log

    def case_ids(self):
        return list(self.traces.keys())

    def iter_traces(self):
        return (
            (case_id, sorted(events, key=lambda event: event.time))
            for case_id, events in self.traces.items()
        )

    def __len__(self):
        return len(self.traces)
