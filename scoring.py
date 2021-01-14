"""This script contains scoring functions and schema matching functions.

TODO: Incorporate entity relation matching score.
"""
from __future__ import annotations

import copy
import glob
import heapq
import os
from typing import List, Tuple
from tqdm import tqdm

def highest_in_matrix(score_matrix: List[List[float]],
                      available_row: List[bool],
                      available_col: List[bool],
                      ) -> Tuple[float, int, int]:
    """Find the highest score in the given matrix / 2D list and return the score
    and its row and column indices.

    Args:
        score_matrix (List[List[float]]): A matrix of scores.
        available_row (List[bool]): A list of boolean values that indicates
        whether a row has been matched.
        available_col (List[bool]): A list of boolean values that indicates
        whether a column has been matched.

    Returns:
        Tuple[float, int, int]: Highest score, row index and column index.
    """
    row_num = len(score_matrix)
    if row_num == 0:
        return 0.0, -1, -1
    col_num = len(score_matrix[0])

    highest_score = 0.0
    row_idx = col_idx = 0
    for i in range(row_num):
        for j in range(col_num):
            if ((available_row[i] and available_col[j])
                    and score_matrix[i][j] > highest_score):
                highest_score = score_matrix[i][j]
                row_idx, col_idx = i, j

    return highest_score, row_idx, col_idx


def get_participant_score(participant_graph,
                          participant_schema,
                          **kwargs) -> float:
    """Calculate the matching score between a participant in the graph and
    a participant in a schema.
    Args:
        participant_graph (Participant): A participant in the graph.
        participant_schema (Participant): A participant in a schema.

    Return:
        float: A score between 0 and 1.
    """
    min_score = kwargs.get('min_score', -100.0)

    role_graph = participant_graph.role
    role_schema = participant_schema.role
    role_graph = role_graph.split('/')[-1]
    role_schema = role_schema.split('/')[-1]

    if role_graph != role_schema:
        return min_score

    # For a participant in the IE graph, entity types is typically a single
    # str instead of a list of str.
    entity_types_graph = participant_graph.entity_types
    entity_types_schema = participant_schema.entity_types
    # if type(entity_types_graph) is list:
    #     raise ValueError('A participant in the IE graph should not be '
    #                      'associated with multiple entity types.')
    if entity_types_graph is not None and entity_types_schema is not None:
        if type(entity_types_graph) is str:
            entity_types_graph = [entity_types_graph]
        if type(entity_types_schema) is str:
            entity_types_schema = [entity_types_schema]
        if len(set(entity_types_graph).intersection(set(entity_types_schema))) > 0:
            return 1.0
        else:
            return kwargs.get('participant_both_entity_score', .5)

    # A participant can also be an event
    type_graph = participant_graph.at_type
    type_shcema = participant_schema.at_type
    if type_graph is not None and type_shcema is not None:
        if type_graph == type_shcema:
            return 1.0
        else:
            return kwargs.get('participant_both_event_score', .5)

    return min_score


def find_participant_matching_greedy(participants_graph: list,
                                     participants_schema: list,
                                     **kwargs
                                     ) -> List[Tuple[float, int, int, str, str]]:
    # TODO: A step have have multiple participants of the same role
    num_graph = len(participants_graph)
    num_schema = len(participants_schema)

    # Calculate the participant matching score matrix, where the i, j element
    # is the score between the i-th participant (of an event) from the graph and
    # the j-th participant from the schema
    matching_scores = [[get_participant_score(participant_graph,
                                              participant_schema,
                                              **kwargs)
                        for participant_schema in participants_schema]
                       for participant_graph in participants_graph]

    # Match participants based on matching scores
    available_row = [True] * num_graph
    available_col = [True] * num_schema
    match = []

    for _ in range(num_graph):
        highest_score, graph_idx, schema_idx = highest_in_matrix(matching_scores,
                                                                 available_row,
                                                                 available_col)
        if highest_score > 0.0:
            match.append((highest_score,
                          graph_idx,
                          schema_idx,
                          participants_graph[graph_idx].at_id,
                          participants_schema[schema_idx].at_id))
            # Update availability
            available_row[graph_idx] = False
            available_col[schema_idx] = False
        else:
            # If the highest score is equal to or smaller than 0, there's no
            # matched participants
            break

    return match


def get_step_score(step_graph,
                   step_schema,
                   **kwargs) -> float:
    """Calculate the matching score between a step in the graph and a
    step in a schema.

    Args:
        step_graph (Step): A step in the graph.
        step_schema (Step): A step in a schema.

    Returns:
        float: A score between 0 and 1.
    """
    type_graph = step_graph.at_type.split('/')[-1]
    type_schema = step_schema.at_type.split('/')[-1]
    min_score = kwargs.get('min_score', -100.0)
    # min_match_level = kwargs.get('min_match_level', 3)
    min_match_level = kwargs.get('min_match_level', 2)
    special_min_match_level = kwargs.get('special_min_match_level', {})
    min_match_level = special_min_match_level.get((type_graph, type_schema),
                                                  min_match_level)

    # Compare event type
    # Split each event type string into event type, subtype, and subsubtype.
    # Example:
    # - In: 'kairos:Primitives/Events/Transaction.ExchangeBuySell.Unspecified'
    # - Out: ['Transaction', 'ExchangeBuySell']
    type_graph_list = (type_graph#.split('/')[-1]
                       .split('.Unspecified')[0]
                       .split('.'))
    type_schema_list = (type_schema#.split('/')[-1]
                        .split('.Unspecified')[0]
                        .split('.'))
    level_num_graph = len(type_graph_list)
    level_num_schema = len(type_schema_list)

    match_case = ('exact' if level_num_graph == level_num_schema
                  # Event type in the schema is less specific
                  else 'less' if level_num_graph > level_num_schema
    # Event type in the schema is more specific
    else 'more')
    # print(type_graph,type_graph_list)
    # print(type_schema,type_schema_list)

    match_level_num = sum(type_graph_list[i] == type_schema_list[i]
                          for i in range(min(level_num_graph, level_num_schema)))
    if match_level_num != min(level_num_graph, level_num_schema):
        match_case = 'unmatched'

    # if step_graph.at_type == 'kairos:Primitives/Events/ArtifactExistence.ManufactureAssemble.Unspecified' and step_schema.at_type == 'kairos:Primitives/Events/ArtifactExistence.ManufactureAssemble.Unspecified':
    #     print(min_match_level)
    
    # Event type matching score
    # if match_case == 'exact':
    #     type_matching_score = kwargs.get('step_type_exact_score', 1.0)
    # elif match_case == 'less':
    #     type_matching_score = kwargs.get('step_type_less_score', 0.5)
    # elif match_case == 'more':
    #     type_matching_score = kwargs.get('step_type_more_score', 0.5)
    # else:
    #     type_matching_score = kwargs.get('step_type_unmatched_score', 0.0)

    # print(match_level_num,min_match_level)
    if match_level_num < min_match_level:
        type_matching_score = min_score
    else:
        type_matching_score = (match_level_num
                               / max(level_num_graph, level_num_schema))

    # Compare participants
    participant_match = find_participant_matching_greedy(
        step_graph.participants, step_schema.participants, **kwargs)
    # TODO: improve the calculation of participant matching score
    participant_matching_score = sum(score for score, _, _, _, _ in participant_match)

    # Calculate step matching score

    if type_matching_score:
        # TODO: discuss about step score
        step_score = type_matching_score + participant_matching_score
        return step_score
    else:
        return min_score


def calculate_sequence_score(steps_graph: list,
                             steps_schema: list,
                             **kwargs) -> float:
    """Calculate the matching score between two sequences.
    Args:
        steps_graph (List[Step]): A list of Step objects from the graph.
        steps_schema (List[Step]): A list of Step objects from the schema.

    Return:
        float: Sequence matching score.
    """
    assert len(steps_graph) == len(steps_schema)

    # Calculate separate step scores
    step_scores = [
        get_step_score(step_graph, step_schema, **kwargs)
        for step_graph, step_schema in zip(steps_graph, steps_schema)
    ]

    total_score = sum(step_scores)

    # Calculate sequence-level scores
    schema = kwargs.get('schema', None)
    graph = kwargs.get('graph', None)
    if schema and graph:
        graph = graph.schema
        # Step indices in the graph/schema
        step_idxs_graph = [graph.get_step_idx(step.at_id)
                           for step in steps_graph]
        step_idxs_schema = [schema.get_step_idx(step.at_id)
                            for step in steps_schema]
        assert all(idx is not None for idx in step_idxs_graph)
        assert all(idx is not None for idx in step_idxs_schema)

        # Calculate coref score
        coref_set_graph = graph.get_coref_set(step_idxs_graph, use_entity=True)
        coref_set_schema = schema.get_coref_set(step_idxs_schema)
        if coref_set_graph and coref_set_schema:
            coref_num = len(coref_set_graph.intersection(coref_set_schema))
            # TODO: other methods to compute coref score
            coref_score = coref_num / len(coref_set_schema)
        else:
            coref_score = 0.0

        # Calculate entity relation score
        entity_rel_set_graph = graph.get_entity_rel_set(step_idxs_graph, use_entity=True)
        entity_rel_set_schema = schema.get_entity_rel_set(step_idxs_schema)
        if entity_rel_set_graph and entity_rel_set_schema:
            entity_rel_num = len(entity_rel_set_graph.intersection(entity_rel_set_schema))
            # TODO: other methods to compute entity relation score
            entity_rel_score = entity_rel_num / len(entity_rel_set_schema)
        else:
            entity_rel_score = 0.0

        # TODO: Linear interpolation for these scores?
        total_score += coref_score + entity_rel_score

    return total_score


def calculate_step_confidence(steps_graph, steps_schema, match):
    """Calculate step condidence scores for matched steps.
    Args:
        steps_graph (List[Step]): A list of steps from the graph.
        steps_schema (List[Step]): A list of steps from the schema.
    Return:
        List[float]: A list of step scores:
    """
    confidence_scores = []
    step_graph_id2idx = {step.at_id: idx for idx, step in enumerate(steps_graph)}
    step_schema_id2idx = {step.at_id: idx for idx, step in enumerate(steps_schema)}
    steps_graph = [steps_graph[step_graph_id2idx[step_id_graph]]
                   for (step_id_graph, _) in match]
    steps_schema = [steps_schema[step_schema_id2idx[step_id_schema]]
                    for (_, step_id_schema) in match]
    # for step_idx_graph, step_idx_schema in match:
        # step_graph = steps_graph[step_idx_graph]
        # step_schema = steps_schema[step_idx_schema]
    for step_graph, step_schema in zip(steps_graph, steps_schema):

        # Event type score
        # Exact match score: 0.8
        # Partial match score: 0.75
        event_type_score = (.8 if step_graph.at_type == step_schema.at_type
                            else .75)

        # Participant score
        # Have common participant(s): 1.0
        # Don't have common participant: 0
        # TODO compare two participant list and check if there are participants
        # of the same role?
        roles_graph = {p.role for p in step_graph.participants}
        roles_schema = {p.role for p in step_schema.participants}
        participant_score = .1 if roles_graph.intersection(roles_schema) else 0

        # Coref score
        coref_score = 0
        for participant_graph in step_graph.participants:
            if participant_graph.refvar:
                participants_schema = [p for p in step_schema.participants
                                       if (p.role == participant_graph.role
                                           and p.refvar)]
                for participant_schema in participants_schema:
                    # for step_idx_graph_tmp, step_idx_schema_tmp in match:
                    for step_graph_tmp, step_schema_tmp in zip(steps_graph, steps_schema):
                        # step_graph_tmp = steps_graph[step_idx_graph_tmp]
                        # step_schema_tmp = steps_graph[step_idx_schema_tmp]

                        if step_graph_tmp.at_id == step_graph.at_id:
                            # Current step
                            continue

                        for participant_graph_tmp in step_graph_tmp.participants:
                            if participant_graph_tmp.refvar == participant_graph.refvar:
                                for participant_schema_tmp in step_schema_tmp.participants:
                                    if (participant_schema_tmp.role == participant_graph_tmp.role
                                        and participant_schema_tmp.refvar == participant_schema.refvar):
                                        coref_score = .1
                                        break

        confidence_scores.append(min(1.0,
                                     event_type_score
                                     + participant_score
                                     + coref_score))
    return confidence_scores






# LCS-based matching algorithm implemented by Haoyang

class HeapNode:
    def __init__(self,
                 matched_graph_items: list,
                 matched_schema_items: list,
                 score: float):
        self.matched_graph_items = copy.deepcopy(matched_graph_items)
        self.matched_schema_items = copy.deepcopy(matched_schema_items)
        self.score = score

    def __lt__(self, other: HeapNode):
        return self.score < other.score

    def __gt__(self, other: HeapNode):
        return self.score > other.score

    def __eq__(self, other: HeapNode):
        return self.score == other.score

    def add_match(self,
                  new_matched_graph_item,
                  new_matched_schema_item,
                  **kwargs):
        matched_graph_items = (copy.deepcopy(self.matched_graph_items)
                               + [new_matched_graph_item])
        matched_schema_items = (copy.deepcopy(self.matched_schema_items)
                                + [new_matched_schema_item])
        # Compute new score
        score = calculate_sequence_score(matched_graph_items,
                                         matched_schema_items,
                                         **kwargs)
        return HeapNode(matched_graph_items, matched_schema_items, score)


def find_best_matching(graph_steps: list,
                       schema_steps: list,
                       beam_size: int = 10,
                       **kwargs) -> Tuple[List[Tuple[int, int]], float]:
    empty_node = HeapNode([], [], calculate_sequence_score([], [], **kwargs))

    dp_table = [[[copy.deepcopy(empty_node)] for _ in range(len(schema_steps))]
                for _ in range(len(graph_steps))]

    max_matching = empty_node
    print('matching schema...')
    for i in tqdm(range(len(graph_steps))):
        for j in range(len(schema_steps)):
            # Transition from i-1, j
            if i > 0:
                for node in dp_table[i - 1][j]:
                    heapq.heappush(dp_table[i][j], copy.deepcopy(node))

            # Transition from i, j-1
            if j > 0:
                for node in dp_table[i][j - 1]:
                    heapq.heappush(dp_table[i][j], copy.deepcopy(node))

            # Transition from i-1, j-1
            if i > 0 and j > 0:
                for node in dp_table[i - 1][j - 1]:
                    augmented_node = node.add_match(graph_steps[i],
                                                    schema_steps[j],
                                                    **kwargs)
                    heapq.heappush(dp_table[i][j], augmented_node)
                    # print([step.at_type for step in augmented_node.matched_graph_items],augmented_node.score)
                    if augmented_node > max_matching:
                        max_matching = augmented_node

            # Special transition for edge cases
            if i == 0 or j == 0:
                augmented_node = empty_node.add_match(graph_steps[i],
                                                      schema_steps[j],
                                                      **kwargs)
                heapq.heappush(dp_table[i][j], augmented_node)
                if augmented_node > max_matching:
                    max_matching = augmented_node

            # Trim the beam set
            while len(dp_table[i][j]) > beam_size:
                heapq.heappop(dp_table[i][j])
    return [(step_graph.at_id, step_schema.at_id)
            for (step_graph, step_schema)
            in zip(max_matching.matched_graph_items,
                   max_matching.matched_schema_items)], max_matching.score

