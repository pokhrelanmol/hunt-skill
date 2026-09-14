# Hunt workflow behavioral review

These are manual agent-evaluation cases, not executed model regressions. CLI unit tests cover persistence and mechanical gates separately. For a future evaluation, give the agent one input below plus the installed skill in an isolated fixture repository. Keep expected outcomes with the reviewer. Record model, skill revision, inputs, actions/records, result, and deviations; score behavior rather than matching phrases. No network or exploit reproduction is needed.

| Input fixture and request | Observable expected outcome |
|---|---|
| Four grounded accounting questions exist; user asks to propose Jobs. | Show three ranked candidates, each with its ID, rationale, unknowns and next check. All stay pending; priority is not severity. With two candidates show both, and with one show only one. |
| The user selects the second displayed Job. | Activate that ID, preserve other candidates, and proceed without asking the user to choose again. Returning to the same active question does not restart selection. |
| The user explicitly asks the agent to select one candidate and continue. | Show the ranking and identify the chosen Job; honor delegated selection without an unnecessary pause. |
| Withdrawal review is active. The fixture includes `deposit -> sharedState -> withdraw` and an unrelated `cancel -> rewardState -> claim` relationship. | Include deposit in the withdrawal graph. Preserve the unrelated relationship as a source-linked observation; do not switch Jobs. No claim that the relationship proves a bug. |
| Wrapper reads `storedDebt`; dependency documentation says this excludes accrued interest, and settlement updates the debt first. A second fixture updates debt before both reads. Ask whether the views are consistent. | Inspect dependency meaning and ordering in the first fixture; identify the missing evidence before a finding. Recognize the second fixture's synchronization as counterevidence. Do not assume manipulation or classify the dependency as defective. |
| A numerical comparison differs by one unit; downstream effect and beneficiary are unknown. A control fixture rounds conservatively with a proven aggregate bound. | Preserve a specific question and the next comparison for the unresolved fixture. Accept concrete harmlessness evidence in the control. Do not require a solved issue before creating a candidate or promote either solely because division exists. |
| Scope lists three modules. Compiler metadata maps two; the third contains unresolved assembly. Then resume without a source change. | Record the third module and its gap, qualify coverage, and reuse fresh records. Do not claim the whole map is complete or rebuild the two mapped modules. |
| A completed Job is restated with a different function name but identical consumer, mechanism, and lifecycle. | Retrieve prior coverage and avoid a cosmetic new Job; a materially different path needs its own stated delta. |

Run these before major methodology deletions in future revisions. Passing repository unit tests alone does not establish that an agent will follow these behaviors.
