from typing import final

from .cases import case, replacement, type_case
from .components import check, edit, fork, new
from .configurations import save
from .gathering import gathering
from .runs import (
    again,
    check_quota,
    queue,
    queue_scoring,
    resume,
    score,
    start,
    start_trials,
)
from .saying import leave, say
from .seen import Seen
from .taking import take, take_from
from .updating import (
    behind_own,
    lineage,
    outdated,
    proposal,
    update,
    update_all,
)


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
    leave = leave

    lineage = lineage
    outdated = outdated
    proposal = proposal
    update = update
    update_all = update_all
    behind_own = behind_own

    start = start
    start_trials = start_trials
    check_quota = check_quota
    again = again
    resume = resume
    queue = queue
    queue_scoring = queue_scoring
    score = score

    gathering = gathering
