# Recovering the tools and reachable resources of an LLM agent in a black-box setting

[Русская версия](README_ru.md)

Year project, 1st year of the "Artificial Intelligence" master's programme, 2026/27 academic year.

| | |
|---|---|
| **Team** | Daria Andreeva |
| **Mentor** | Albina Burlova |
| **Academic advisor** | Albina Burlova |
| **Track** | research? |

---

## What the project is about

An LLM agent has a system prompt, a set of tools with parameter schemas, and data it can reach through those tools. From the outside, only the dialogue is visible. We measure how much of this configuration can be recovered with access to the dialogue alone, and how many queries that costs.

The goal is practical: the recovered agent profile is meant for automatic test generation, not for attack. To test an agent, you need to know what it can actually do, not what its documentation claims.

### Research questions

1. **Completeness.** What share of tools, schema fields and reachable resources can be recovered under a fixed query budget?
2. **Channel.** Does using the agent's own tools as a probing channel (for example, validation errors that reveal the schema) improve recall over asking directly?
3. **Stopping.** Can we estimate during probing that everything has been recovered, and stop?
4. **Distinguishability.** Which configurations (RAG or no RAG, one agent or several, tool classes and permissions) cannot be told apart from the outside with any number of queries?

### How this differs from existing work

- Prompt extraction work (Zhang et al., JustAsk, output2prompt) recovers text and does not use the target's tools.
- Work on extracting data through tools (ToolSiphon, RAG-Thief) measures the share of records pulled out, but does not build an agent profile.
- Work that builds a graph (AGENTEVAL, ChainFuzzer) either recovers only dialogue-level behaviour or requires access to the code.
- None of them has a completeness criterion ("everything has been extracted"): the budget is either fixed, or stopping is tied to the reproducibility of the answer rather than to ground truth.

## Core concepts

| Set | What it is |
|---|---|
| **Declared** | Tools and schemas described in the agent's configuration |
| **Reachable** | What the agent can actually call or read within the user's permissions: reproduced in k out of R runs |
| **Observed** | What probing managed to recover |

Main metrics: recall and precision of the observed set against the reachable set, over tools, schema fields and resources, as a function of the number of queries.

## Work plan

| # | Stage | Deadline | What we do | Outcome |
|---|---|---|---|---|
| 1 | Kick-off and planning | 6 October | Topic, plan, repository | This README |
| 2 | Exploratory analysis | 27 October | Build a testbed of 3–5 agent configurations with known ground truth (candidates: τ-bench, AgentDojo). Pilot: what the agent reveals when asked directly | Testbed, labelled declared and reachable sets, description of observable signals |
| 3 | Metrics and baselines | 27 November | Fix the metrics. Baselines: direct query, multi-step strategy search, passive dialogue exploration | "Recall vs. number of queries" curves for each baseline |
| 4 | Service | 15 December | FastAPI service: takes an agent endpoint and a query budget, returns the agent profile as JSON | Working service running the best baseline |
| | **Interim defence** | 10–15 January | Survey of the field, testbed, baseline results, plan for the second semester | Presentation |
| 5 | Our method | 15 March | Probing through the agent's own tools and adaptive query selection: keep a set of hypotheses about the configuration, pick the next query to eliminate as many as possible | Comparison with baselines under an equal budget |
| 6 | Learned component | 5 May | Classifier of configurations from agent responses. If it cannot separate two configurations, that is empirical evidence they are indistinguishable | Map of distinguishable and indistinguishable configurations |
| 7 | Final refinements | TBD | Stopping criterion, robustness to defences and noisy tool descriptions, error analysis, experiment reproducibility (MLflow) | Reproducible set of experiments |
| | **Final defence** | 13–20 June | Results for the year | Presentation |

Deadlines for checkpoints 2–7 are tentative and will be confirmed by the programme.

### Out of scope

- Faithfulness of agent reports (the agent says the task is done when it is not). This needs an oracle over the backend state and is a separate problem.
- Attacks on real production systems. All experiments run on our own testbed.

## Risks

| Risk | Mitigation |
|---|---|
| Building the testbed eats up the schedule | Take an existing benchmark and vary only the configurations |
| The method does not work on rigidly scripted agents | Record this as a limit of applicability rather than trying to work around it |
| Asking directly already reveals almost everything | Add configurations with defences and hidden resources, where the baseline degrades |

## References

- Zhang, Carlini, Ippolito. *Effective Prompt Extraction from Language Models.* [arXiv:2307.06865](https://arxiv.org/abs/2307.06865)
- *JustAsk.* [arXiv:2601.21233](https://arxiv.org/abs/2601.21233)
- *output2prompt.* [arXiv:2405.15012](https://arxiv.org/abs/2405.15012)
- *KYA.* [arXiv:2607.19837](https://arxiv.org/abs/2607.19837)
- *ToolSiphon.* [arXiv:2608.30288](https://arxiv.org/abs/2608.30288)
- *AGENTEVAL.* [arXiv:2607.06873](https://arxiv.org/abs/2607.06873)
- *ChainFuzzer.* [arXiv:2603.12614](https://arxiv.org/abs/2603.12614)
- *CIA.* [ACL 2026](https://aclanthology.org/2026.acl-long.815.pdf)

## Repository structure

```
├── README.md
├── docs/          # literature survey, presentations
├── stand/         # agent configurations and ground-truth labels
├── probing/       # baselines and our method
├── service/       # FastAPI service
└── experiments/   # notebooks and results
```