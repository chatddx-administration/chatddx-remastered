from typing import final

from .cases import (
    appendices_of,
    appendix,
    carry,
    case,
    case_titled,
    case_titles,
    replacement,
    type_case,
)
from .components import component, edit_component, fork_component, new
from .configurations import edit, fork, save
from .following import follow, proposal
from .runs import score, start
from .saying import say
from .seen import Seen
from .taking import take, take_from


@final
class Bench(Seen):
    save = save
    fork = fork
    edit = edit

    component = staticmethod(component)
    new = new
    fork_component = fork_component
    edit_component = edit_component

    appendix = appendix
    case = case
    case_titled = case_titled
    case_titles = case_titles
    appendices_of = appendices_of
    replacement = replacement
    type_case = type_case
    carry = carry

    take = take
    take_from = take_from

    say = say

    proposal = proposal
    follow = follow

    start = start
    score = score
