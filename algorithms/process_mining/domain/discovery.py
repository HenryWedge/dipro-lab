from pm4py.discovery import discover_petri_net_alpha, discover_petri_net_heuristics, discover_petri_net_inductive

from process_mining.domain.petri_net import DiscoveredPetriNet


class Discovery:
    def discover_alpha(self, pm4py_log, activity_key: str = 'concept:name',
                       case_id_key: str = 'case:concept:name',
                       timestamp_key: str = 'time:timestamp') -> DiscoveredPetriNet:
        net, im, fm = discover_petri_net_alpha(
            pm4py_log, activity_key=activity_key,
            case_id_key=case_id_key,
            timestamp_key=timestamp_key)

        return DiscoveredPetriNet(
            algorithm='alpha',
            parameters={},
            net=net,
            initial_marking=im,
            final_marking=fm
        )

    def discover_heuristics(self, pm4py_log, dependency_threshold: float, activity_key: str = 'concept:name',
                            case_id_key: str = 'case:concept:name',
                            timestamp_key: str = 'time:timestamp') -> DiscoveredPetriNet:
        net, im, fm = discover_petri_net_heuristics(
            pm4py_log, activity_key=activity_key,
            case_id_key=case_id_key,
            timestamp_key=timestamp_key,
            dependency_threshold=dependency_threshold
        )

        return DiscoveredPetriNet(
            algorithm='heuristics',
            parameters={'dependency_threshold': dependency_threshold},
            net=net,
            initial_marking=im,
            final_marking=fm
        )

    def discover_inductive(self, pm4py_log, activity_key: str = 'concept:name',
                           case_id_key: str = 'case:concept:name',
                           timestamp_key: str = 'time:timestamp') -> DiscoveredPetriNet:
        net, im, fm = discover_petri_net_inductive(
            pm4py_log, activity_key=activity_key,
            case_id_key=case_id_key,
            timestamp_key=timestamp_key
        )

        return DiscoveredPetriNet(
            algorithm='inductive',
            parameters={},
            net=net,
            initial_marking=im,
            final_marking=fm
        )
