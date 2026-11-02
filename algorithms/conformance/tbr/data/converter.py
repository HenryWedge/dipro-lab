import pandas as pd
from pm4py.objects.log.obj import Event as Pm4PyEvent
from pm4py.objects.log.obj import EventLog as Pm4PyEventLog
from pm4py.objects.log.obj import Trace

from .event import Event
from .event_log import EventLog


class Converter:
    def to_event_log(self, event_log: Pm4PyEventLog, location_key=None, skip_events_without_location=True):
        converted_log = EventLog()
        for trace in event_log:
            case_id = self.case_id_from_trace(trace)
            for pm4py_event in trace:
                if skip_events_without_location and location_key and location_key not in pm4py_event:
                    continue
                converted_log.add_event(
                    self.to_event(pm4py_event, case_id, location_key=location_key)
                )
        return converted_log

    def to_event(self, pm4py_event, case_id, location_key=None):
        location = self.read_optional_value(pm4py_event, location_key, default="")
        return Event(
            case_id=case_id,
            activity=str(pm4py_event["concept:name"]),
            location=str(location),
            time=pm4py_event["time:timestamp"],
        )

    def from_event_log(self, event_log):
        pm4py_log = Pm4PyEventLog()
        for case_id, events in event_log.iter_traces():
            trace = Trace()
            trace.attributes["concept:name"] = case_id
            for event in events:
                trace.append(self.from_event(event))
            pm4py_log.append(trace)
        return pm4py_log

    def from_event(self, event):
        pm4py_event = Pm4PyEvent()
        pm4py_event["concept:name"] = event.activity
        pm4py_event["time:timestamp"] = pd.Timestamp(event.time)
        pm4py_event["case:concept:name"] = event.case_id
        pm4py_event["location"] = event.location
        return pm4py_event

    def case_id_from_trace(self, trace):
        return str(trace.attributes["concept:name"])

    def read_optional_value(self, event, key, default):
        if key and key in event:
            return event[key]
        return default
