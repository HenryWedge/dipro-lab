import random
from pathlib import Path

from process_mining.adapters.pm4py.converter import Converter

class EventLogSplitter:
    def __init__(self, file_path=None, event_log=None, training_split=0.8, location_key=None, random_seed=1):
        self.converter = Converter()
        self.training_split = training_split
        self.location_key = location_key
        self.random_seed = random_seed
        self.log = event_log if event_log is not None else self.read_xes_log(file_path, location_key)
        self.case_ids = self.log.case_ids()
        self.split_index = self.calculate_split_index()

    def read_xes_log(self, file_path, location_key):
        import pm4py

        pm4py_log = pm4py.read_xes(str(Path(file_path)), return_legacy_log_object=True)
        return self.converter.to_event_log(pm4py_log, location_key=location_key)

    def calculate_split_index(self):
        random.Random(self.random_seed).shuffle(self.case_ids)
        return int(len(self.case_ids) * self.training_split)

    def split(self):
        return (
            self.log.filter_case_ids(self.case_ids[: self.split_index]),
            self.log.filter_case_ids(self.case_ids[self.split_index :]),
        )
