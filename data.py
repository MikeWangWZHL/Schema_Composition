"""This script define data class for IE graph files, TA1 output files, and TA2 output file.

TODO: Move the `update_participants()` function out of this script to avoid importing from `scoring`.
TODO: Update the definition of Graph.
TODO: Update some classes (e.g., Relation) based on the latest format.
"""
from __future__ import annotations
from copy import deepcopy

from itertools import combinations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Sized, Tuple, Any, Union, Set

import copy
import json
import logging
from queue import Queue
from itertools import product

from scoring import find_participant_matching_greedy

logger = logging.getLogger(__name__)


@dataclass
class Provenance:
    # at_id: str
    provenance: str
    child_id: str
    media_type: str = 'text/plain'
    offset: int = -1
    length: int = -1
    comment: Union[str, List[str]] = None
    bounding_box: List[int] = None
    start_time: float = -1.0
    end_time: float = -1.0
    key_frames: List[int] = None

    def __post_init__(self):
        if self.comment is None:
            self.comment = ''

    @staticmethod
    def from_dict(provenance_dict) -> Provenance:
        if 'provenance' in provenance_dict:
            provenance_id = provenance_dict['provenance']
        elif '@id' in provenance_dict:
            provenance_id = provenance_dict['@id']
        else:
            raise ValueError('Either provenance or @id is required')
        return Provenance(provenance=provenance_id,
                          comment=provenance_dict.get('comment', ''),
                          child_id=provenance_dict['childID'],
                          media_type=provenance_dict.get('mediaType',
                                                         'text/plain'),
                          offset=provenance_dict.get('offset', -1),
                          length=provenance_dict.get('length', -1),
                          bounding_box=provenance_dict.get(
                              'boundingBox', None),
                          start_time=provenance_dict.get('startTime', -1.0),
                          end_time=provenance_dict.get('endTime', -1.0),
                          key_frames=provenance_dict.get('keyFrames', None))

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        # Required fields
        provenance_dict = {'provenance': self.provenance,
                           'childID': self.child_id,
                           'mediaType': self.media_type}
        # Optional fields
        if self.comment:
            provenance_dict['comment'] = self.comment
        if self.offset >= 0:
            provenance_dict['offset'] = self.offset
            provenance_dict['length'] = self.length
        if self.bounding_box:
            provenance_dict['boundingBox'] = self.bounding_box
        if self.start_time >= 0:
            provenance_dict['startTime'] = self.start_time
        if self.end_time >= 0:
            provenance_dict['endTime'] = self.end_time
        if self.key_frames:
            provenance_dict['keyFrames'] = self.key_frames

        return provenance_dict


@dataclass
class Value:
    # name: str
    entity_type: str
    provenance: Union[str, List[str]]
    entity: str = None
    at_type: str = None
    confidence: Union[str, float] = -1.0
    comment: str = None

    @staticmethod
    def from_dict(value_dict: Dict[str, Any]) -> Value:
        return Value(
            # name=value_dict['name'],
            entity_type=value_dict.get('entity_type', None),
            at_type=value_dict.get('@type', None),
            confidence=value_dict.get('confidence', -1.0),
            provenance=value_dict['provenance'],
            comment=value_dict.get('comment', None),
            entity=value_dict.get('entity', None),
        )

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        # Required fields
        value_dict = {  # 'name': self.name,
            'provenance': self.provenance}
        # Optional fields
        if self.entity:
            value_dict['entity'] = self.entity
        if self.entity_type:
            value_dict['entityType'] = self.entity_type
        if self.at_type:
            value_dict['@type'] = self.at_type
        if type(self.confidence) is str or self.confidence >= 0:
            value_dict['confidence'] = self.confidence
        if self.comment:
            value_dict['comment'] = self.comment
        return value_dict


@dataclass
class Participant:
    at_id: str
    name: str
    role: str
    refvar: str = None
    entity: str = None
    entity_types: Union[str, List[str]] = None
    at_type: str = None
    values: List[Dict[str, Any]] = None
    _meta: Dict[str, Any] = None

    def __post_init__(self):
        if self.entity_types is None and self.at_type is None:
            logger.warning(
                'Either entityTypes or @type should be provided: ' + self.name)
        if self._meta is None:
            self._meta = {}

    @staticmethod
    def from_dict(participant_dict: Dict[str, Any]) -> Participant:
        if 'role' not in participant_dict:
            print(participant_dict)
        values = participant_dict.get('values', [])
        if values is None:
            values = []
        return Participant(at_id=participant_dict['@id'],
                           name=participant_dict['name'],
                           role=participant_dict['role'],
                           refvar=participant_dict.get('refvar', None),
                           entity=participant_dict.get('entity', None),
                           entity_types=participant_dict.get(
                               'entityTypes', None),
                           at_type=participant_dict.get('@type', None),
                           #    values=participant_dict.get('values', None)
                           values=[Value.from_dict(value)
                                   for value in values]
                           )

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        # Required
        participant_dict = {'@id': self.at_id,
                            'name': self.name,
                            'role': self.role}
        # Optional
        if self.refvar:
            participant_dict['refvar'] = self.refvar
        if self.entity:
            participant_dict['entity'] = self.entity
        if self.entity_types:
            participant_dict['entityTypes'] = self.entity_types
        if self.at_type:
            participant_dict['@type'] = self.at_type
        # if self.values or kwargs.get('output_participant_values', False):
            # participant_dict['values'] = ([] if self.values is None
            #   else self.values)
        if self.values:  # or kwargs.get('output_participant_values', False):
            participant_dict['values'] = ([] if self.values is None
                                          else [v.to_dict(**kwargs) for v in self.values])

        return participant_dict

    @property
    def types(self):
        if self.entity_types:
            if type(self.entity_types) is str:
                return [self.entity_types]
            else:
                return self.entity_types
        elif self.at_type:
            return [self.at_type]
        else:
            return []

    def copy(self) -> Participant:
        return Participant(at_id=self.at_id,
                           name=self.name,
                           role=self.role,
                           refvar=self.refvar,
                           entity_types=(None if self.entity_types is None
                                         else copy.deepcopy(self.entity_types)),
                           at_type=self.at_type,
                           values=(None if self.values is None
                                   else copy.deepcopy(self.values)),
                           _meta=self._meta
                           )

    def filling_coref(self, participang_other):
        if self.refvar != participang_other.refvar or self.refvar == None:
            return False
        if self.values != None and len(self.values) > 0:
            return False
        if participang_other.values == None or len(participang_other.values) == 0:
            return False
        self.name = participang_other.name
        self.entity_types = participang_other.entity_types
        self.values = participang_other.values
        return True


@dataclass
class Step:
    at_id: str
    name: str
    at_type: str
    aka: List[str] = None
    comment: Union[str, List[str]] = None
    participants: List[Participant] = None
    confidence: Union[str, float] = -1.0
    temporal: List[Dict[str, str]] = None
    provenance: str = None
    _meta: Dict[str, Any] = None
    # Added in v0.9
    ta1ref: str = None
    modality: List[str] = None
    min_duration: str = None
    max_duration: str = None

    def __post_init__(self):
        if self.participants is None:
            self.participants = []
        if self.modality is None:
            self.modality = []
        if self._meta is None:
            self._meta = {}
        # if self.temporal is not None:
        #     for temporal_item in self.temporal:
        #         if 'confidence' not in temporal_item:
        #             temporal_item['confidence'] = 1.0

    @staticmethod
    def from_dict(step_dict: Dict[str, Any]) -> Step:
        participants = step_dict.get('participants', [])
        return Step(at_id=step_dict['@id'],
                    name=step_dict['name'],
                    at_type=step_dict['@type'],
                    aka=step_dict.get('aka', None),
                    comment=step_dict.get('comment', None),
                    participants=[Participant.from_dict(p)
                                  for p in participants],
                    confidence=step_dict.get('confidence', -1.0),
                    temporal=step_dict.get('temporal', []),
                    provenance=step_dict.get('provenance', None),
                    ta1ref=step_dict.get('ta1ref', None),
                    modality=[],
                    # modality=step_dict.get('modality', None),
                    min_duration=step_dict.get('minDuration', None),
                    max_duration=step_dict.get('maxDuration', None)
                    )

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        # Required
        step_dict = {'@id': self.at_id,
                     'name': self.name,
                     '@type': self.at_type,
                     'participants': [p.to_dict(**kwargs) for p in self.participants],
                     }
        # Optional
        if self.aka:
            step_dict['aka'] = self.aka
        if self.comment:
            step_dict['comment'] = self.comment
        if type(self.confidence) is str or self.confidence >= 0:
            step_dict['confidence'] = self.confidence
        if self.temporal:
            step_dict['temporal'] = self.temporal
        if self.provenance:
            step_dict['provenance'] = self.provenance
        if self.ta1ref:
            step_dict['ta1ref'] = self.ta1ref
        if self.min_duration:
            step_dict['minDuration'] = self.min_duration
        if self.max_duration:
            step_dict['maxDuration'] = self.max_duration
        if self.modality:
            modality = [x for x in self.modality if x != 'actual']
            step_dict['modality'] = modality

        return step_dict

    @property
    def source(self) -> str:
        return self._meta.get('source', None)

    def copy(self) -> Step:
        return Step(
            self.at_id,
            self.name,
            self.at_type,
            aka=None if self.aka is None else copy.deepcopy(self.aka),
            comment=None if self.comment is None else copy.deepcopy(
                self.comment),
            participants=(None if self.participants is None
                          else [p.copy() for p in self.participants]),
            confidence=self.confidence,
            temporal=(None if self.temporal is None
                      else copy.deepcopy(self.temporal)),
            provenance=self.provenance,
            min_duration=self.min_duration,
            max_duration=self.max_duration,
            modality=self.modality
        )

    def copy_to_ta2(self, schema_step: bool = True) -> Step:
        """Copy a step to TA2 output.
        Args:
            schema_step (bool): This step is from a TA1 schema. Defaults to True.
        Returns:
            Step: Copied step.
        """
        # Update @id
        step = Step(
            self.at_id,
            self.name,
            self.at_type,
            aka=None if self.aka is None else copy.deepcopy(self.aka),
            comment=None if self.comment is None else copy.deepcopy(
                self.comment),
            participants=(None if self.participants is None
                          else [p.copy() for p in self.participants]),
            temporal=(None if self.temporal is None
                      else copy.deepcopy(self.temporal)),
            provenance='{}.prov'.format(self.at_id) if schema_step else self.provenance,
            confidence=1.0,
            ta1ref=self.at_id if schema_step else 'kairos:NULL',
            min_duration=self.min_duration,
            max_duration=self.max_duration,
            modality=self.modality,
            _meta=self._meta,
        )

        if schema_step:
            step._meta['source'] = 'schema'
        else:
            step._meta['source'] = 'graph'

        return step

    def update_participants(self,
                            step_other: Step,
                            match,
                            allowed_roles,
                            allowed_entity_types,
                            role_mapping,
                            **kwargs) -> List[Participant]:
        """Update the participant list.

        Args:
            step_other (Step): A step from graph G.

        Returns:
            List[Participant]: An updated list of participants.

        TODO: it's probably better to move this function to instantiate.py
        """
        def is_valid_role(participant, event_type):
            role = participant.role.split('/')[-1]
            valid = role in allowed_roles[event_type]
            # if not valid:
                # print('Removed role {}:{}'.format(event_type, role))
            return valid

        def revise_role(participant, event_type_other, event_type_self):
            role = participant.role.split('/')[-1]
            role = role_mapping.get((event_type_other, event_type_self, role), role)

            participant.role = '{}/Slots/{}'.format(self.at_type,
                                                    role)
            return True

        def revise_entity_type(participant, event_type_self):
            def get_entity_type(ori_entity_type: str):
                entity_type = ori_entity_type.split('/')[-1]
                role = participant.role.split('/')[-1]
                role_allowed_entity_types = allowed_entity_types.get((event_type_self, role), None)
                if role_allowed_entity_types:
                    if entity_type not in role_allowed_entity_types:
                        if entity_type == 'VEH' and 'WEA' in role_allowed_entity_types:
                            entity_type = 'WEA'
                            # print('VEH -> WEA')
                        elif entity_type == 'WEA' and 'VEH' in role_allowed_entity_types:
                            entity_type = 'VEH'
                            # print('WEA -> VEH')
                        else:
                            entity_type = next(iter(role_allowed_entity_types))
                            # print('-> {}'.format(entity_type))
                    entity_type = 'kairos:Primitives/Entities/{}'.format(entity_type)
                    return entity_type
                return ori_entity_type
                    
                    
            entity_types = participant.entity_types
            if type(entity_types) is list:
                participant.entity_types = [get_entity_type(entity_type) for entity_type in entity_types]
            else:
                participant.entity_types = get_entity_type(entity_types)

        # Update participants
        matched_participants_other = {at_id for _, _, _, at_id, _ in match}
        matched_participants_self = {at_id for _, _, _, _, at_id in match}

        event_type_other = step_other.at_type.split('/')[-1]
        event_type_self = self.at_type.split('/')[-1]

        participants_new = []
        # Add matched participants
        for _, idx_other, idx_self, _, _ in match:
            participant_other = step_other.participants[idx_other]
            participant_self = self.participants[idx_self]
            participant_new = Participant(
                participant_self.at_id,
                participant_other.name,
                participant_self.role,
                refvar=(participant_other.refvar
                        if participant_other.refvar
                        else participant_self.refvar),
                entity=participant_self.entity,
                # entity_types=participant_self.entity_types,
                entity_types=participant_other.entity_types,
                at_type=participant_self.at_type,
                values=participant_other.values,
                _meta={'matched': True,
                       'graph_at_id': participant_other.at_id,
                       'graph_refvar': participant_other.refvar
                       }
            )
            revise_role(participant_new,
                        event_type_other,
                        event_type_self)
            # if not valid_role:
            #     continue
            if not is_valid_role(participant_new, event_type_self):
                continue
            revise_entity_type(participant_new, event_type_self)

            participants_new.append(participant_new)

        # TODO: Can be simplified using list comprehension
        # Add other participants in TA1 schema
        for participant in self.participants:
            if participant.at_id not in matched_participants_self:
                participant_new = participant.copy()

                if not is_valid_role(participant_new, event_type_self):
                    continue

                participant_new._meta['source'] = 'schema'
                participants_new.append(participant_new)

        # Add other participants in graph G
        for participant in step_other.participants:
            if participant.at_id not in matched_participants_other:
                participant_new = participant.copy()
                # Update prefixes
                # TODO: if the Participant_0 is matched to Participant_1 in the
                # schema, when I merge Participant_1 from the graph, should I
                # change its index, e.g., Particpant_1 -> Participant_2
                # Here I add a suffix _graph to avoid duplication
                revise_role(participant_new,
                            event_type_other,
                            event_type_self)
                # if not valid_role:
                    # continue
                if not is_valid_role(participant_new, event_type_self):
                    continue
                revise_entity_type(participant_new, event_type_self)

                participant_new._meta['source'] = 'graph'
                participants_new.append(participant_new)

        return participants_new

    def instantiate(self,
                    step_other: Step,
                    participant_match,
                    allowed_entity_types,
                    allowed_roles,
                    role_mapping,
                    **kwargs) -> Step:
        """Instantiate a step.
        TODO: it's probably better to move this function to instantiate.py

        Args:
            step_other (Step): A step from graph G.

        Returns:
            Step: The instantiated step.
        """
        updated_participants = self.update_participants(step_other,
                                                        participant_match,
                                                        allowed_entity_types=allowed_entity_types,
                                                        allowed_roles=allowed_roles,
                                                        role_mapping=role_mapping,
                                                        **kwargs)
        step = Step(
            self.at_id,
            step_other.name,
            self.at_type,
            aka=self.aka,
            comment=self.comment,
            temporal=step_other.temporal,
            provenance=step_other.provenance,
            participants=updated_participants,
            confidence=kwargs.get('confidence', 1.0),
            ta1ref=self.at_id,
            min_duration=self.min_duration,
            max_duration=self.max_duration,
            modality=self.modality,
            _meta=self._meta
        )
        step._meta['source'] = 'both'
        return step

    def fill_participants(self, ontology):
        event_type = self.at_type.split('/')[-1]
        existing_roles = {p.role.split('/')[-1] for p in self.participants}
        expected_roles = ontology[event_type]
        for role, entity_types in expected_roles:
            if role not in existing_roles:
                self.participants.append(Participant(
                    at_id='{}/Slot/{}_0'.format(self.at_id, role),
                    name='{}_0'.format(role),
                    role='kairos:Primitives/Events/{}/Slots/{}'.format(
                        event_type, role),
                    entity_types=['kairos:Primitives/Entities/{}'.format(e)
                                  for e in entity_types],  # if e != 'EVENT'],
                ))
    
    def filling_coref(self, step_other):
        if self.ta1ref == "kairos:NULL" or step_other.ta1ref == "kairos:NULL":
            return
        if (not self.ta1ref) or (not step_other.ta1ref):
            return
        if (not "matched" in self._meta) or (not self._meta["matched"]):
            return
        if (not "matched" in step_other._meta) or (not step_other._meta["matched"]):
            return
        for participant in self.participants:
            for participant_other in step_other.participants:
                if participant.filling_coref(participant_other):
                    # TODO: Adding logging for propagated participants
                    pass

    def get_participant_ids(self, source='both'):
        if source == 'graph':
            return [(None, p.at_id) for p in self.participants]
        elif source == 'schema':
            return [(p.at_id, None) for p in self.participants]
        elif source == 'both':
            participants = []
            for p in self.participants:
                if p._meta.get('matched', False):
                    participants.append((p.at_id, p._meta['graph_at_id']))
                elif p._meta.get('source', None) == 'graph':
                    participants.append((None, p.at_id))
                    # print(p.at_id)
                elif p._meta.get('source', None) == 'schema':
                    participants.append((p.at_id, None))
                else:
                    logger.warning('Hmm, not sure where this particpant is from')
            return participants
        else:
            logger.error('Unknown source: {}'.format(source))
            return []

    def print(self):
        print('@id:', self.at_id)
        print('name:', self.name)
        print('event type:', self.at_type.split('/')[-1])
        if self.participants:
            for participant in self.participants:
                print('- {}: {}'.format(participant.role.split('/')[-1],
                                     participant.name))

    def remove_event_participants(self):
        participants = []
        for participant in self.participants:
            if participant.entity_types != 'kairos:Primitives/Entities/EVENT':
                participants.append(participant)
            else:
                print('remove {}'.format(participant.name))
        self.participants = participants


@dataclass
class Order:
    """Define the temporal order between a step (a list of steps) and another
    step (another list of steps)."""
    before: Union[str, List[str]]
    after: Union[str, List[str]]
    at_id: str = None
    ta1ref: str = None
    comment: Union[str, List[str]] = None
    confidence: float = 1.0
    flags: str = None

    @staticmethod
    def from_dict(order_dict: Dict[str, Any]) -> Order:
        return Order(before=order_dict['before'],
                     after=order_dict['after'],
                     ta1ref=order_dict.get('ta1ref', None),
                     comment=order_dict.get('comment', None),
                     confidence=order_dict.get('confidence', 1.0),
                     flags=order_dict.get('flags', None),
                     at_id=order_dict.get('@id', None)
                     )

    def to_dict(self) -> Dict[str, Any]:
        order_dict = {'before': self.before,
                      'after': self.after,
                      'confidence': self.confidence
                      }
        if self.at_id:
            order_dict['@id'] = self.at_id
        if self.ta1ref:
            order_dict['ta1ref'] = self.ta1ref
        if self.comment:
            order_dict['comment'] = self.comment
        if self.flags:
            order_dict['flags'] = self.flags

        return order_dict

    def get_ordered_pairs(self) -> List[Tuple[str, str]]:
        before = self.before if type(self.before) is list else [self.before]
        after = self.after if type(self.after) is list else [self.after]
        return [(b, a) for b in before for a in after]

    def set_ta1ref(self, is_from_ta1: bool = True):
        if is_from_ta1:
            self.ta1ref = self.at_id
        else:
            self.ta1ref = 'kairos:NULL'

    def update_ids(self, id_mapping):
        if type(self.before) is str:
            self.before = id_mapping.get(self.before, self.before)
        else:
            self.before = [id_mapping.get(x, x) for x in self.before]

        if type(self.after) is str:
            self.after = id_mapping.get(self.after, self.after)
        else:
            self.after = [id_mapping.get(x, x) for x in self.after]

    def remove_invalid_steps(self, steps):
        if type(self.before) is str:
            if self.before not in steps:
                return False
        else:
            before = [x for x in self.before if x in steps]
            if len(before) == 0:
                return False
            self.before = before
        if type(self.after) is str:
            if self.after not in steps:
                return False
        else:
            after = [x for x in self.after if x in steps]
            if len(after) == 0:
                return False
            self.after = after
        return True


@dataclass
class Slot:
    at_id: str
    role_name: str
    entity_types: Union[str, List[str]]
    super_: str = None
    refvar: str = None
    aka: str = None

    @staticmethod
    def from_dict(slot_dict: Dict[str, Any]) -> Slot:
        return Slot(at_id=slot_dict['@id'],
                    role_name=slot_dict['roleName'],
                    refvar=slot_dict.get('refvar', None),
                    aka=slot_dict.get('aka', None),
                    entity_types=slot_dict['entityTypes'],
                    super_=slot_dict.get('super', None))

    def to_dict(self) -> Dict[str, Any]:
        # Required fields
        slot_dict = {'@id': self.at_id,
                     'roleName': self.role_name,
                     'entityTypes': self.entity_types}
        # Optional fields
        if self.refvar:
            slot_dict['refvar'] = self.refvar
        if self.aka:
            slot_dict['aka'] = self.aka
        if self.super_:
            slot_dict['super'] = self.super_

        return slot_dict


@dataclass
class Entity:
    at_id: str
    name: str
    entity_types: Union[str, List[str]]
    refvar: str = None
    comment: Union[str, List[str]] = None
    reference: str = None

    @staticmethod
    def from_dict(entity_dict: Dict[str, Any]) -> Entity:
        if 'entityTypes' in entity_dict:
            entity_types = entity_dict['entityTypes']
        elif 'entityTypes_AND' in entity_dict:
            entity_types = entity_dict['entityTypes_AND']
        else:
            raise ValueError('entityTypes or entityTypes_AND is required')

        return Entity(at_id=entity_dict['@id'],
                      name=entity_dict['name'],
                      entity_types=entity_types,
                      refvar=entity_dict.get('refvar', None),
                      comment=entity_dict.get('comment', None),
                      reference=entity_dict.get('reference', None)
                      )

    def to_dict(self) -> Dict[str, Any]:
        entity_dict = {'@id': self.at_id,
                       'name': self.name,
                       'entityTypes': self.entity_types,
                       }
        if self.refvar:
            entity_dict['refvar'] = self.refvar
        if self.comment:
            entity_dict['comment'] = self.comment
        if self.reference:
            entity_dict['reference'] = self.reference

        return entity_dict


@dataclass
class Relation:
    name: str
    relation_predicate: str
    relation_object: str
    # Added in v0.9
    at_id: str = None
    ta1ref: str = None
    confidence: float = 1.0
    provenance: str = None
    relation_provenance: str = None

    @staticmethod
    def from_dict(relation_dict: Dict[str, Any]) -> Relation:
        return Relation(at_id=relation_dict.get('@id', None),
                        name=relation_dict.get('name', 'untitled_relation'),
                        relation_predicate=relation_dict['relationPredicate'],
                        relation_object=relation_dict['relationObject'],
                        ta1ref=relation_dict.get('ta1ref', None),
                        confidence=relation_dict.get('confidence', 1.0),
                        provenance=relation_dict.get('provenance', None),
                        relation_provenance=relation_dict.get(
                            'relationProvenance', None)
                        )

    def to_dict(self) -> Dict[str, Any]:
        relation_dict = {'name': self.name,
                         'relationPredicate': self.relation_predicate,
                         'relationObject': self.relation_object,
                         'confidence': self.confidence
                         }
        if self.at_id:
            relation_dict['@id'] = self.at_id
        if self.ta1ref:
            relation_dict['ta1ref'] = self.ta1ref
        if self.provenance:
            relation_dict['provenance'] = self.provenance
        if self.relation_provenance:
            relation_dict['relationProvenance'] = self.relation_provenance
        return relation_dict

    def copy(self):
        return Relation(name=self.name,
                        relation_predicate=self.relation_predicate,
                        relation_object=self.relation_object,
                        at_id=self.at_id,
                        ta1ref=self.ta1ref,
                        confidence=self.confidence,
                        provenance=self.confidence,
                        relation_provenance=self.relation_provenance)


@dataclass
class EntityRelation:
    relation_subject: str
    comment: Union[str, List[str]]
    relations: Union[Relation, List[Relation]]
    provenance: str = None

    @staticmethod
    def from_dict(entity_relation_dict: Dict[str, Any]) -> EntityRelation:
        if type(entity_relation_dict['relations']) is list:
            # relations is a list: before v0.9
            relations = [Relation.from_dict(rel)
                         for rel in entity_relation_dict['relations']]
        else:
            # relations is a dict: v0.9
            relations = Relation.from_dict(entity_relation_dict['relations'])
        return EntityRelation(
            relation_subject=entity_relation_dict['relationSubject'],
            comment=entity_relation_dict.get('commnet', ''),
            provenance=entity_relation_dict.get('provenance', None),
            # relations=[Relation.from_dict(relation)
            #    for relation in entity_relation_dict['relations']]
            relations=relations
        )

    @property
    def relation_object(self):
        if type(self.relations) is list:
            return self.relations[0].relation_object
        return self.relations.relation_object

    def update_object(self, object):
        assert type(self.relations) is not list
        self.relations.relation_object = object

    def copy(self):
        if type(self.relations) is list:
            relations = [r.copy() for r in self.relations]
        else:
            relations = self.relations.copy()
        return EntityRelation(relation_subject=self.relation_subject,
                              comment=deepcopy(self.comment),
                              relations=relations,
                              provenance=self.provenance)

    def to_dict(self) -> Dict[str, Any]:
        if type(self.relations) is list:
            logger.warning(
                'After v0.92 "relations" should be a dict not a list')
            if len(self.relations) == 1:
                relations = self.relations[0].to_dict()
            else:
                relations = [relation.to_dict() for relation in self.relations]
        else:
            relations = self.relations.to_dict()

        entity_relation_dict = {'relationSubject': self.relation_subject,
                                'comment': self.comment,
                                'relations': relations}
        if self.provenance:
            entity_relation_dict['provenance'] = self.provenance

        return entity_relation_dict


@dataclass
class Primitive:
    at_id: str
    version: str
    super_: str
    name: str
    description: str
    reference: str
    min_duration: str
    max_duration: str
    template: str
    slots: List[Slot]
    aka: Union[str, List[str]] = None

    @staticmethod
    def from_dict(primitive_dict: Dict[str, Any]) -> Primitive:
        return Primitive(at_id=primitive_dict['@id'],
                         version=primitive_dict['version'],
                         super_=primitive_dict['super'],
                         name=primitive_dict['name'],
                         description=primitive_dict['description'],
                         aka=primitive_dict.get('aka', None),
                         reference=primitive_dict.get('reference'),
                         min_duration=primitive_dict.get('minDuration'),
                         max_duration=primitive_dict.get('maxDuration'),
                         template=primitive_dict.get('template'),
                         slots=[Slot.from_dict(slot)
                                for slot in primitive_dict['slots']],
                         )

    def to_dict(self) -> Dict[str, Any]:
        # Required fields
        primitive_dict = {'@id': self.at_id,
                          'version': self.version,
                          'super': self.super_,
                          'name': self.name,
                          'description': self.description,
                          'reference': self.reference,
                          'minDuration': self.min_duration,
                          'maxDuration': self.max_duration,
                          'template': self.template,
                          'slot': [slot.to_dict() for slot in self.slot],
                          }
        # Optional fields
        if self.aka:
            primitive_dict['aka'] = self.aka

        return primitive_dict


@dataclass
class Schema:
    at_id: str
    name: str
    description: str
    version: str
    steps: List[Step]
    order: List[Order] = None
    slots: List[Slot] = None
    entities: List[Entity] = None
    private_data: Dict[str, str] = None
    comment: Union[str, List[str]] = None
    entity_relations: List[EntityRelation] = None
    provenance_data: List[Provenance] = None
    confidence: Union[str, float] = -1.0
    super_: str = None

    def __post_init__(self):
        if self.private_data is None:
            self.private_data = {}
        self.step_id2idx = {step.at_id: idx
                            for idx, step in enumerate(self.steps)}
        self.participants = {participant.at_id: (idx, participant.role)
                             for idx, step in enumerate(self.steps)
                             for participant in step.participants}
        if self.order is None:
            self.order = []
        if self.entity_relations is None:
            self.entity_relations = []
        self.check_duplicated_ids()

    @staticmethod
    def from_dict(schema_dict: Dict[str, Any]) -> Schema:
        steps = [Step.from_dict(step)
                             for step in schema_dict['steps']]
        steps = [step for step in steps if not step.at_type.endswith('Personnel.Elect')]

        return Schema(at_id=schema_dict['@id'],
                      name=schema_dict['name'],
                      description=schema_dict['description'],
                      version=schema_dict.get('version', ''),
                      private_data=schema_dict.get('privateData', {}),
                      steps=[Step.from_dict(step)
                             for step in schema_dict['steps']],
                      order=[Order.from_dict(order)
                             for order in schema_dict.get('order', [])],
                      slots=[Slot.from_dict(slot)
                             for slot in schema_dict.get('slots', [])],
                      entities=[Entity.from_dict(entity)
                                for entity in schema_dict.get('entities', [])],
                      comment=schema_dict.get('comment', None),
                      entity_relations=[EntityRelation.from_dict(rel)
                                        for rel in schema_dict.get('entityRelations', [])],
                      #   entity_relations=[],
                      provenance_data=[
                          Provenance.from_dict(prov)
                          for prov in schema_dict.get('provenanceData', [])],
                      confidence=schema_dict.get('confidence', -1.0),
                      )

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        # Required fields
        schema_dict = {'@id': self.at_id,
                       'name': self.name,
                       'description': self.description,
                       'version': self.version,
                       'steps': [step.to_dict(**kwargs) for step in self.steps],
                       }
        # Optional fields
        if self.private_data:
            schema_dict['privateData'] = self.private_data
        else:
            schema_dict['privateData'] = {}

        if self.slots:
            schema_dict['slots'] = [slot.to_dict() for slot in self.slots]
        else:
            schema_dict['slots'] = []

        if self.entities:
            schema_dict['entities'] = [entity.to_dict()
                                       for entity in self.entities]
        else:
            schema_dict['entities'] = []

        if self.order:
            schema_dict['order'] = [order.to_dict() for order in self.order]
        else:
            schema_dict['order'] = []

        if self.comment:
            schema_dict['comment'] = self.comment
        if self.entity_relations:
            schema_dict['entityRelations'] = [rel.to_dict()
                                              for rel in self.entity_relations]
        else:
            schema_dict['entityRelations'] = []
        if self.provenance_data:
            schema_dict['provenanceData'] = [prov.to_dict()
                                             for prov in self.provenance_data]
        if type(self.confidence) is str or self.confidence >= 0:
            schema_dict['confidence'] = self.confidence
        if self.super_:
            schema_dict['super'] = self.super_

        return schema_dict

    def get_ordered_steps(self, ignore_order: bool = True) -> List[Step]:
        """Get an ordered list of steps.
        TODO: Update this function if there are other types of temporal
        relations.

        Returns:
            List[Step]: A list of Step objects.
        """
        if self.order and not ignore_order:
            edges = defaultdict(list)
            in_degree = defaultdict(int)
            for order in self.order:
                for before, after in order.get_ordered_pairs():
                    edges[before].append(after)
                    in_degree[after] += 1
            q = Queue()
            steps = {step.at_id: step for step in self.steps}
            for step in self.steps:
                if in_degree[step.at_id] == 0:
                    q.put(step.at_id)
            ordered_steps = []
            while not q.empty():
                step_id = q.get()
                ordered_steps.append(steps[step_id])
                for edge in edges[step_id]:
                    in_degree[edge] -= 1
                    if in_degree[edge] == 0:
                        q.put(edge)

            return ordered_steps
        else:
            return self.steps

    def get_step_idx(self, step_id: str) -> int:
        """Get the index of a step given the step ID. None is returned if no
        step matches the step ID.

        Args:
            step_id (str): Step ID.

        Returns:
            int: Step index.
        """
        return self.step_id2idx.get(step_id, None)

    def get_coref_set(self,
                      step_idxs: List[int],
                      use_entity: bool = False,
                      ) -> Set[Tuple[int, str, int, str]]:
        """Get a set of coreferential participants.
        Each element in the returned set is a tuple (i, role_1, j, role_2) which
        represents that the participant with role_1 of the i-th step in
        step_idxs is coreferential with the argument with role_2 of the j-sth
        step in step_idxs.

        Args:
            step_idxs (List[int]): A list of step indices.
            use_entity (bool):

        Returns:
            Set[Tuple[int, str, int, str]]: A set of coreferential participants.
        """
        if len(step_idxs) <= 1:
            return []

        coref_participants = defaultdict(set)
        for i, step_idx in enumerate(step_idxs):
            participants = self.steps[step_idx].participants
            for participant in participants:
                if use_entity:
                    for value in participant.values:
                        coref_participants[value.entity].add(
                            (i, participant.role))
                else:
                    if participant.refvar:
                        coref_participants[participant.refvar].add(
                            (i, participant.role))

        coref_set = set()
        for participants in coref_participants.values():
            for (i, role_1), (j, role_2) in combinations(participants, 2):
                if i == 0:
                    continue
                if i > j:
                    i, j, role_1, role_2 = j, i, role_2, role_1
                coref_set.add((i, role_1, j, role_2))

        return coref_set

    def get_entity_rel_set(self,
                           step_idxs: List[int],
                           use_entity: bool = False,
                           ) -> Set[Tuple[int, str, str, int, str]]:
        """Get a set of entity pairs and their entity relations.
        Each element in the returned set is a tuple (i, role_1, predicate, j, role_2) which
        represents that the participant with role_1 of the i-th step in
        step_idxs has an entity relation with type of predicate with the argument with role_2 of the j-sth
        step in step_idxs.

        Args:
            step_idxs (List[int]): A list of step indices.
            use_entity (bool):

        Returns:
            Set[Tuple[int, str, str, int, str]]: A set of coreferential participants.
        """
        if len(step_idxs) <= 1:
            return []

        entity_mapping = defaultdict(set)
        for i, step_idx in enumerate(step_idxs):
            participants = self.steps[step_idx].participants
            for participant in participants:
                if use_entity:
                    for value in participant.values:
                        entity_mapping[value.entity].add(
                            (i, participant.role))
                else:
                    entity_mapping[participant.at_id].add(
                        (i, participant.role))

        entity_rel_set = set()
        for entity_relation in self.entity_relations:
            subject_id = entity_relation.relation_subject
            if type(entity_relation.relations) is list:
                # relations is a list: before v0.9
                relations = entity_relation.relations
            else:
                # relations is a dict: v0.9
                relations = [entity_relation.relations]
            for relation in relations:
                predicate = relation.relation_predicate
                object_id = relation.relation_object
                # TODO: Add support for relation before v0.9
                if type(entity_relation.relations) is list:
                    object_id = object_id[0]
                for subject_info, object_info in product(entity_mapping[subject_id], entity_mapping[object_id]):
                    entity_rel_set.add((*subject_info, predicate, *object_info))

        return entity_rel_set

    def check_duplicated_ids(self):
        step_ids = {step.at_id for step in self.steps}
        if len(step_ids) != len(self.steps):
            logger.warning('schema {} has duplicated step ids'.format(self.at_id))

    def uniquify_participants(self):
        participant_id_map = {}
        for step in self.steps:
            for participant in step.participants:
                participant_id = participant.at_id
                participant_id_new = '{}_{}'.format(participant_id,
                                                    len(participant_id_map))
                participant_id_map[participant_id] = participant_id_new
                participant.at_id = participant_id_new
        for entity_relation in self.entity_relations:
            subj = entity_relation.relation_subject
            entity_relation.relation_subject = participant_id_map.get(subj, subj)
            relations = entity_relation.relations
            if type(relations) is list:
                for relation in relations:
                    obj = relation.relation_object
                    relation.relation_object = participant_id_map.get(obj, obj)
            else:
                obj = entity_relation.relation_object
                entity_relation.relations.relation_object = participant_id_map.get(obj, obj)


@dataclass
class TA1:
    at_context: Union[str, List[Any]]
    at_id: str
    schemas: List[Schema]
    sdf_version: str = '0.81'

    @staticmethod
    def from_dict(ta1_dict: Dict[str, Any]) -> TA1:
        return TA1(at_context=ta1_dict['@context'],
                   at_id=ta1_dict['@id'],
                   sdf_version=ta1_dict['sdfVersion'],
                   schemas=[Schema.from_dict(schema)
                            for schema in ta1_dict['schemas']])

    @staticmethod
    def from_file(path: str) -> TA1:
        return TA1.from_dict(json.load(open(path)))

    @staticmethod
    def from_data(data: str) -> TA1:
        return TA1.from_dict(json.loads(data))

    def to_dict(self) -> Dict[str, Any]:
        return {
            '@context': self.at_context,
            '@id': self.at_id,
            'sdfVersion': self.sdf_version,
            'schemas': [schema.to_dict() for schema in self.schemas],
        }

    def uniquify_participants(self):
        for schema in self.schemas:
            schema.uniquify_participants()


@dataclass
class TA2:
    at_context: Union[str, List[Any]]
    at_id: str
    sdf_version: str
    primitives: List[Primitive]
    schemas: List[Schema]
    task2: bool = False

    @staticmethod
    def from_dict(ta2_dict: Dict[str, Any]) -> TA2:
        return TA2(at_context=ta2_dict['@context'],
                   at_id=ta2_dict['@id'],
                   sdf_version=ta2_dict['sdfVersion'],
                   primitives=[Primitive.from_dict(primitive)
                               for primitive in ta2_dict.get('primitives', [])],
                   schemas=[Schema.from_dict(schema)
                            for schema in ta2_dict['schemas']],
                   task2 = ta2_dict.get("task2", False)
                   )

    @staticmethod
    def from_file(path: str) -> TA2:
        return TA2.from_dict(json.load(open(path)))

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        ta2_dict = {'@context': self.at_context,
                    '@id': self.at_id,
                    'sdfVersion': self.sdf_version,
                    'ta2': True,
                    'primitives': [primitive.to_dict()
                                   for primitive in self.primitives],
                    'schemas': [schema.to_dict(output_participant_values=True)
                                for schema in self.schemas],
                    'task2': self.task2
                    }
        # if self.primitives:
        # ta2_dict['primitives'] = [primitive.to_dict()
        #   for primitive in self.primitives]
        return ta2_dict

    def print(self):
        print(json.dumps(self.to_dict(), indent=2))

    def save(self, path: str, indent: int = 2):
        json.dump(self.to_dict(), open(path, 'w'), indent=indent)


@dataclass
class Graph:
    at_context: Union[str, List[Any]]
    at_id: str
    sdf_version: str
    schemas: List[Schema]
    _data: str = None
    
    def __post_init__(self):
        self.remove_event_participants()

    @staticmethod
    def from_dict(graph_dict: Dict[str, Any], data_str=None) -> Graph:
        return Graph(at_context=graph_dict['@context'],
                     at_id=graph_dict['@id'],
                     sdf_version=graph_dict['sdfVersion'],
                     schemas=[Schema.from_dict(schema)
                              for schema in graph_dict['schemas']],
                     _data=data_str
                     )

    @staticmethod
    def from_file(path: str) -> Graph:
        with open(path) as r:
            data = r.read()
        return Graph.from_data(data)

    @staticmethod
    def from_data(data: str) -> Graph:
        return Graph.from_dict(json.loads(data), data)

    def clone(self):
        return Graph.from_data(self._data)

    def to_dict(self) -> Dict[str, Any]:
        return {'@context': self.at_context,
                '@id': self.at_id,
                'sdfVersion': self.sdf_version,
                'ta2': False,
                'schemas': [schema.to_dict() for schema in self.schemas],
                }

    @property
    def schema(self) -> Schema:
        return self.schemas[0]

    def print(self):
        print(json.dumps(self.to_dict(), indent=2))
        
    def remove_event_participants(self):
        for schema in self.schemas:
            for step in schema.steps:
                step.remove_event_participants()
