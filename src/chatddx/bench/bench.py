from typing import final

from .cases import appendix, carry, case, replacement, type_case
from .components import component, edit_component, fork_component, new
from .configurations import edit, fork, save
from .following import follow, proposal
from .runs import score, start
from .saying import say
from .taking import take, take_from
from .view import View


# What one person sees and does: the View's reads, and the writes, each bound from the
# module that holds it. The functions are imported rather than their modules, since
# `from . import` would import this package again from inside it, and `@final` spares
# each binding an annotation.
@final
class Bench(View):
    save = save
    fork = fork
    edit = edit

    component = staticmethod(component)
    new = new
    fork_component = fork_component
    edit_component = edit_component

    appendix = appendix
    case = case
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
