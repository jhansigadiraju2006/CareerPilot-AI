import json
from agents.agents import (
    CareerAgent, SkillAgent, LearningAgent, ResumeAgent,
    PlacementAgent, InterviewAgent, ProjectAgent
)
from db import get_db
from ollama_client import generate


class Orchestrator:
    def __init__(self, uid):
        self.uid = uid
        self.agents = [
            CareerAgent(), SkillAgent(), LearningAgent(),
            ResumeAgent(), PlacementAgent(), InterviewAgent(),
            ProjectAgent()
        ]

    def log(self, agent, action, status="completed", details=""):
        with get_db() as c:
            c.execute(
                "INSERT INTO activities(user_id,agent,action,status,details) "
                "VALUES(?,?,?,?,?)",
                (self.uid, agent, action, status, str(details)[:3000])
            )

    def create_plan(self, profile):
        allowed_agents = {
            "Career Agent",
            "Skill Agent",
            "Learning Agent",
            "Resume Agent",
            "Placement Agent",
            "Interview Agent",
            "Project Agent",
        }

        prompt = (
            "Return one valid JSON object only. No Markdown and no extra text. "
            "The JSON must contain exactly these top-level keys: goal, tasks, verification. "
            "Each item in tasks must contain exactly these keys: agent, action, reason. "
            "The agent value must be exactly one of these strings: "
            "'Career Agent', 'Skill Agent', 'Learning Agent', 'Resume Agent', "
            "'Placement Agent', 'Interview Agent', 'Project Agent'. "
            "Never write 'task' instead of 'agent'. Never add the word Agent to an agent name. "
            "Example of a valid task: "
            '{"agent":"Skill Agent","action":"Identify skill gaps",'
            '"reason":"Compare current skills with target-role requirements"}. '
            "Include 3 to 7 tasks. Prioritize the student's target role and skill gaps. "
            "Do not claim tasks have already run. "
            "Student profile: "
            + json.dumps(profile, ensure_ascii=False, default=str)[:3000]
        )
        raw, ai_ok = generate(
            prompt,
            system=(
                "You are CareerPilot's planning agent. "
                "Output only valid JSON. Never invent student achievements. "
                "Choose tasks that can be handled by the listed agents."
            )
        )

        plan_data = None

        if ai_ok and raw:
            try:
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                    if cleaned.rstrip().endswith("```"):
                        cleaned = cleaned.rstrip()[:-3].strip()

                start = cleaned.find("{")
                end = cleaned.rfind("}")
                if start != -1 and end > start:
                    plan_data = json.loads(cleaned[start:end + 1])

                if not isinstance(plan_data, dict):
                    plan_data = None

                if plan_data is not None:
                    tasks = plan_data.get("tasks")
                    if not isinstance(tasks, list) or not tasks:
                        plan_data = None
                    else:
                        valid_tasks = []
                        for task in tasks:
                            if not isinstance(task, dict):
                                continue
                            agent_name = task.get("agent")
                            action = task.get("action")
                            if agent_name in allowed_agents and isinstance(action, str) and action.strip():
                                valid_tasks.append({
                                    "agent": agent_name,
                                    "action": action.strip()[:200],
                                    "reason": str(task.get("reason", ""))[:300]
                                })

                        if not valid_tasks:
                            plan_data = None
                        else:
                            plan_data["tasks"] = valid_tasks[:7]
                            plan_data["goal"] = str(
                                plan_data.get("goal") or
                                profile.get("target_role") or
                                "Software Developer"
                            )[:300]
                            plan_data["verification"] = str(
                                plan_data.get("verification") or
                                "Verify each executed task has a result."
                            )[:500]

            except (ValueError, TypeError, AttributeError):
                plan_data = None

        if plan_data is not None:
            mode = "llm_planned"
            ai_used = True
        else:
            mode = "rule_based_fallback"
            ai_used = False
            plan_data = {
                "goal": profile.get("target_role") or "Software Developer",
                "tasks": [
                    {
                        "agent": "Skill Agent",
                        "action": "Identify skill gaps",
                        "reason": "Find skills required for the target role."
                    },
                    {
                        "agent": "Learning Agent",
                        "action": "Prioritize learning",
                        "reason": "Turn skill gaps into learning priorities."
                    },
                    {
                        "agent": "Resume Agent",
                        "action": "Review profile evidence",
                        "reason": "Identify missing portfolio evidence."
                    },
                    {
                        "agent": "Placement Agent",
                        "action": "Estimate placement readiness",
                        "reason": "Identify preparation priorities."
                    }
                ],
                "verification": "Confirm each executed task returns a result."
            }

        plan_json = json.dumps(plan_data, ensure_ascii=False)

        self.log(
            "Planner Agent",
            "Created validated career execution plan",
            mode,
            plan_json
        )

        return {
            "mode": mode,
            "plan": plan_data,
            "ai_used": ai_used
        }
    

    
    def analyze(self, profile):
        plan_info = self.create_plan(profile)
        plan = plan_info["plan"]
        planned_tasks = plan.get("tasks", [])

        context = {"profile": profile}
        output = {}
        steps = []
        executed_agents = []

        result_keys = {
            "Career Agent": "career_agent",
            "Skill Agent": "skills",
            "Learning Agent": "learning",
            "Resume Agent": "resume_agent",
            "Placement Agent": "placement_agent",
            "Interview Agent": "interview_agent",
            "Project Agent": "project_agent"
        }

        dependencies = {
            "Career Agent": set(),
            "Skill Agent": set(),
            "Learning Agent": {"Skill Agent"},
            "Resume Agent": {"Skill Agent"},
            "Placement Agent": {"Skill Agent", "Resume Agent"},
            "Interview Agent": set(),
            "Project Agent": {"Skill Agent"}
        }

        default_order = [
            "Career Agent", "Skill Agent", "Learning Agent",
            "Resume Agent", "Placement Agent", "Interview Agent",
            "Project Agent"
        ]

        agent_by_name = {agent.name: agent for agent in self.agents}
        plan_rank = {}

        for task in planned_tasks:
            name = task.get("agent")
            if name in agent_by_name and name not in plan_rank:
                plan_rank[name] = len(plan_rank)

        pending = set(agent_by_name)

        while pending:
            ready = [
                name for name in pending
                if dependencies[name].issubset(set(executed_agents))
            ]

            if not ready:
                raise RuntimeError(
                    "Unable to resolve specialist-agent dependencies."
                )

            chosen = min(
                ready,
                key=lambda name: (
                    plan_rank.get(name, 999),
                    default_order.index(name)
                )
            )

            agent = agent_by_name[chosen]
            key = result_keys[chosen]

            matching_tasks = [
                task for task in planned_tasks
                if task.get("agent") == chosen
            ]
            planned_task = matching_tasks[0] if matching_tasks else None

            action = (
                planned_task["action"]
                if planned_task
                else "Supporting specialist analysis"
            )

            step = {
                "agent": chosen,
                "action": action,
                "status": "running",
                "planned": planned_task is not None
            }

            if planned_task:
                step["reason"] = planned_task.get("reason", "")

            try:
                result = agent.run(context)

                if not isinstance(result, dict):
                    raise TypeError("Agent must return a dictionary.")

                output[key] = result
                context[key] = result

                if chosen == "Skill Agent":
                    context["skills"] = result

                step["status"] = "completed"
                step["result_keys"] = list(result.keys())

                self.log(
                    chosen,
                    "Mapped planned task to specialist analysis"
                    if planned_task
                    else "Executed supporting specialist analysis",
                    "completed",
                    json.dumps(
                        {
                            "planned_action": action,
                            "analysis_result": result
                        },
                        ensure_ascii=False,
                        default=str
                    )
                )

            except Exception as exc:
                step["status"] = "failed"
                step["error"] = f"{type(exc).__name__}: {exc}"

                self.log(
                    chosen,
                    "Specialist analysis failed",
                    "error",
                    step["error"]
                )

                steps.append(step)
                raise

            steps.append(step)
            executed_agents.append(chosen)
            pending.remove(chosen)

        skill_result = output["skills"]
        resume_result = output["resume_agent"]
        learning_result = output["learning"]
        readiness = output["placement_agent"]["readiness"]

        output["digital_twin"] = {
            "current": profile.get("skills", ""),
            "target": profile.get("target_role", ""),
            "gaps": skill_result["gaps"],
            "readiness": readiness,
            "next_actions": learning_result["weekly_focus"]
        }

        output["summary"] = (
            f"Target: {profile.get('target_role') or 'Software Developer'}. "
            f"Skill coverage is {skill_result['coverage']}%, "
            f"portfolio health is {resume_result['health']}%, and "
            f"placement readiness is {readiness}%. "
            f"Priority gaps: "
            f"{', '.join(skill_result['gaps'][:4]) or 'None'}."
        )

        output["explainability"] = [
            {
                "factor": "Skill coverage",
                "value": skill_result["coverage"],
                "reason": "Measures matched target-role skills."
            },
            {
                "factor": "Portfolio health",
                "value": resume_result["health"],
                "reason": (
                    "Checks available project, certification "
                    "and skill evidence."
                )
            },
            {
                "factor": "Placement readiness",
                "value": readiness,
                "reason": (
                    "Combines skill coverage, portfolio evidence "
                    "and experience level."
                )
            }
        ]

        planned_results = []

        for task in planned_tasks:
            name = task.get("agent")
            result_key = result_keys.get(name)
            result = output.get(result_key) if result_key else None

            planned_results.append({
                "agent": name,
                "action": task.get("action", ""),
                "reason": task.get("reason", ""),
                "status": (
                    "analysis_generated"
                    if isinstance(result, dict)
                    else "not_mapped"
                ),
                "result_keys": (
                    list(result.keys())
                    if isinstance(result, dict)
                    else []
                ),
                "note": (
                    "Specialist analysis generated; "
                    "the described real-world task is not "
                    "confirmed as completed."
                )
            })

        output["agentic_execution"] = {
            "planner": plan_info["mode"],
            "plan": plan,
            "ai_used": plan_info["ai_used"],
            "steps": steps,
            "planned_tasks": planned_results,
            "completed": sum(
                step["status"] == "completed" for step in steps
            ),
            "failed": sum(
                step["status"] == "failed" for step in steps
            ),
            "total": len(steps)
        }

        return output
