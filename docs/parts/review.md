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

A run button that queues a case centered gathering with 3 replicates and 1 repeat, and leads back to the page as it was:
nothing of what ran is shown, and the button is disabled while a run of the case is queued or under way.

## Gatherings

Below the run button the page holds nothing, the table of each configuration's scores and the list of its answers gone.
`/runs` and `/scores/{score}/{case}/{replicate}/{view}` show what ran.

## Measuring the yardstick

Before a clinician asks how a case fared, they ask whether its expectation measures what they meant: a pattern too broad
scores every answer well, one too narrow none. Review shows beside each target how it has scored, then brings up that
pattern alone and how it has matched, or not, against the texts it has read.

It stays on the review page, not a page of its own: the case is what the target belongs to, and the Expectation pane
beside it is where it gets fixed.
