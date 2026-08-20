


## Project Structure

All team members should follow the agreed project structure below
as closely as possible.

New files or folders should only be added when required by the
implementation, and should be placed in the appropriate existing
module.

```text
kayfa-content-approval-pipeline/
│
├── app/                              # Member 4 — Streamlit
│   ├── Home.py
│   └── pages/
│       ├── 1_Draft_Review.py
│       ├── 2_Version_History.py
│       ├── 3_Evaluation.py
│       ├── 4_Security.py
│       └── 5_Cost_Observability.py
│
├── api/                              # Member 3 — FastAPI
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   └── schemas.py
│
├── src/
│   ├── __init__.py
│   │
│   ├── schemas.py                    # Member 1 — Pydantic models
│   │
│   ├── agent/                        # Member 1 — LangGraph
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── graph.py
│   │   ├── prompts.py
│   │   ├── persistence.py
│   │   └── publisher.py
│   │
│   ├── retrieval/                    # Member 2 — LlamaIndex
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── index.py
│   │   ├── retrieve.py
│   │   └── evaluation.py
│   │
│   ├── security/                     # Member 4
│   │   ├── __init__.py
│   │   ├── guards.py
│   │   └── red_team.py
│   │
│   ├── observability/                # Member 3
│   │   ├── __init__.py
│   │   ├── tracing.py
│   │   ├── metrics.py
│   │   └── toon_benchmark.py
│   │
│   └── evals/                        # Member 4
│       ├── __init__.py
│       ├── dataset.py
│       ├── metrics.py
│       └── runner.py
│
├── data/
│   ├── knowledge_base/               # Member 2
│   │   ├── brand_style_guide.md
│   │   ├── approved_examples/
│   │   │   ├── example_01.md
│   │   │   ├── example_02.md
│   │   │   └── ...
│   │   └── briefs/
│   │       ├── brief_01.md
│   │       ├── brief_02.md
│   │       └── poisoned_brief.md
│   │
│   └── eval/
│       ├── test_briefs.md
│       └── expected_results.json
│
├── reports/
│   ├── evaluation_report.md
│   ├── failure_mode_analysis.md
│   ├── security_report.md
│   ├── cost_observability_toon.md
│   └── framework_justification.md
│
├── tests/
│   ├── test_schemas.py
│   ├── test_drafter.py
│   ├── test_style_critic.py
│   ├── test_reviser.py
│   ├── test_graph.py
│   └── test_workflow.py
│
├── automation/
│   └── workflow.json
│
├── README.md
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
└── .env                              # NEVER commit


## Agent Workflow — Member 1

The central workflow is implemented using LangGraph.

### Workflow

```mermaid
flowchart TD
    A[Brief Submitted] --> B[Drafter]
    B --> C[Style Critic]
    C --> D[Human Review]

    D -->|Approve| E[Publisher]
    E --> F[Published Markdown]

    D -->|Reject| G[Reviser]
    G --> C

    D -->|Edit| H[Apply Human Edit]
    H --> C

    D -->|Reject at MAX_REVISIONS| I[Escalation]
    I --> J[END]

    D -.->|HITL Interrupt| D