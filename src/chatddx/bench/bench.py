from typing import final

from .cases import case, replacement, type_case
from .components import check, edit, fork, new
from .configurations import save
from .following import follow, follow_moved, lineage, moved, proposal
from .runs import again, queue, queue_scoring, resume, score, start
from .saying import say
from .seen import Seen
from .taking import take, take_from


@final
class Bench(Seen):
    new = new
    fork = fork
    edit = edit
    save = save
    check = check

    case = case
    replacement = replacement
    type_case = type_case

    take = take
    take_from = take_from

    say = say

    proposal = proposal
    lineage = lineage
    follow = follow
    moved = moved
    follow_moved = follow_moved

    start = start
    again = again
    resume = resume
    queue = queue
    queue_scoring = queue_scoring
    score = score
