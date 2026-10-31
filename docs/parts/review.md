# Review

Drafted: `/review/{family}` (`src/chatddx/portal/review.py`; `src/chatddx/portal/test/test_reviewing.py`), its frontend
in `frontend/src/lib/review/`.

Review is a family (vignette), appendices, expectations and Gatherings centered on case. Its purpose is to provide the
means for a the clinician to assess whether the expectation's intention and application align. The page consists of
three columns filling the viewport: Tree, Vignette and Expectations.

The Tree lists each family, with its cases of appendices as branches under it filtered in place by tags and languages.

Vignette shows the vignette and managages appendices.

Expectations manages the notes and patterns associated with each view: Differential diagnoses, warnings (red flags),
disposition, must not be missed and a medical statement from a clinician. It has a shallow version shifter that prefills
the fields on change with confirmation. What a scorer can't read, like a pattern that doesn't parse, is told below its
field, marked in a collapsed field's header, and can't be saved.

A restore button restores all fields to their stored values. Saves save it all. If appendices have changed this is now
another case. Fields for tags and languages visually scuffed but exist.

If the case chosen is with an appendix that the user owns it can be deleted and shows a delete button.

<<<<<<< signed
A run button that queues a case centered gathering with 3 replicates and 1 repeat, and leads back to the page as it was:
nothing of what ran is shown, and the button is disabled while a run of the case is queued or under way.
=======
A run button that brings the case to a whole gathering of 3 replicates and 1 repeat under each of the person's
configurations as things are now, and leads back to the page as it was. It is disabled while a run of the case is queued
or under way, and, once How the case fares has read, while nothing is behind that a run mends.
>>>>>>> @stamp

## Gatherings

<<<<<<< signed
Below the run button the page holds nothing, the table of each configuration's scores and the list of its answers gone.
`/runs` and `/scores/{score}/{case}/{replicate}/{view}` show what ran.
=======
A case's latest gathering under a configuration is the runs started together with its latest run reaching it
(`src/chatddx/bench/gathering.py:gatherings`): what How the case fares plots and what Run mends. Under each
configuration it is either a whole 3+1 as things are now or behind (`src/chatddx/api/standing.py:standing`):

- under way, which Run waits for;
- out of date, untranslated or refused by the gate, which Run can't mend;
- no runs, not a whole 3+1, its configuration changed since, or halted, which Run runs again, on the same seeds where it
  has them;
- stopped before it finished, which Run resumes;
- not scored against the expectation as it is, which Run scores again.

## How the case fares

Below the page, read once scrolled near, then again while a run of the case is under way: where each configuration
stands, then, by field and view, each configuration's mean on this case among every other case's latest under it. A
configuration behind marks its value, and each replicate the mean is made of is a point linking to its score.
>>>>>>> @stamp

## Measuring the yardstick

Before a clinician asks how a case fared, they ask whether its expectation measures what they meant: a pattern too broad
scores every answer well, one too narrow none. Review shows beside each target how it has scored, then brings up that
pattern alone and how it has matched, or not, against the texts it has read.

It stays on the review page, not a page of its own: the case is what the target belongs to, and the Expectation pane
beside it is where it gets fixed.
