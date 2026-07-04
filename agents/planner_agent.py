"""
agents/planner_agent.py
Study Planner Agent

Responsibilities:
  - Create personalised study schedules
  - Accept exam date, available study hours, and subjects
  - Generate daily / weekly study plans
  - Include revision and spaced-repetition recommendations
"""

import logging
from config.ibm_config import generate_text, AGENT_INSTRUCTIONS

logger = logging.getLogger(__name__)

_STRATEGY = AGENT_INSTRUCTIONS["study_planning_strategy"]
_LEVEL = AGENT_INSTRUCTIONS["academic_level"]
_STYLE = AGENT_INSTRUCTIONS["teaching_style"]


class StudyPlannerAgent:
    """
    Agent 5 – Study Planner Agent

    Collaborates with other agents: receives topic lists from the
    Summarization Agent and builds personalised schedules using
    IBM Granite reasoning.
    """

    # ── Public API ───────────────────────────────────────────

    def create_study_plan(
        self,
        subject: str,
        exam_date: str,
        daily_hours: float,
        topics: str = "",
        current_level: str = "beginner",
    ) -> str:
        """
        Generate a detailed personalised study plan.

        Args:
            subject:       Subject or course name.
            exam_date:     Target exam date (e.g. "2024-12-15").
            daily_hours:   Hours available per day.
            topics:        Comma-separated list of topics to cover.
            current_level: Student's self-assessed level.
        """
        topics_section = (
            f"\nTopics to cover: {topics}" if topics else ""
        )
        prompt = f"""You are a Study Planner Agent – an expert academic coach.
Strategy: {_STRATEGY}
Academic level: {_LEVEL}
Teaching style: {_STYLE}

Create a detailed personalised study plan for:
- Subject: {subject}
- Exam Date: {exam_date}
- Daily study hours available: {daily_hours} hours
- Student's current level: {current_level}{topics_section}

Include:
## 📅 Study Plan for {subject}

**Overview**
- Total days until exam: [calculate]
- Total study hours available: [calculate]
- Recommended daily breakdown

**Week-by-Week Plan**
For each week:
  - Week [N] – Theme/Focus
  - Daily tasks (Mon–Sun)
  - Topics to cover
  - Practice activities

**Revision Strategy**
- When to start revision
- Spaced repetition schedule
- Mock exam timing

**Daily Study Template**
- Morning / Afternoon / Evening slots
- Short breaks (Pomodoro technique)

**Exam Week Plan**
- Final revision checklist
- Day-before strategy
- Exam-day tips

STUDY PLAN:"""
        logger.info(
            "PlannerAgent: creating study plan for '%s', exam on %s.",
            subject,
            exam_date,
        )
        return generate_text(prompt)

    def generate_weekly_schedule(
        self,
        subjects: list,
        daily_hours: float,
        week_number: int = 1,
    ) -> str:
        """
        Generate a single-week timetable for multiple subjects.

        Args:
            subjects:    List of subject names.
            daily_hours: Total study hours available per day.
            week_number: Which week this is (affects intensity).
        """
        subjects_str = ", ".join(subjects) if subjects else "General Study"
        prompt = f"""You are a Study Planner Agent.
Strategy: {_STRATEGY}

Create a detailed Week {week_number} study timetable.
Subjects: {subjects_str}
Daily hours available: {daily_hours}

Format as a day-by-day schedule (Monday to Sunday).
For each day list:
- Morning session (subject + task)
- Afternoon session (subject + task)
- Evening session (review/practice)
- Rest / free time

Balance subjects fairly and include at least one rest day.

WEEK {week_number} TIMETABLE:"""
        logger.info(
            "PlannerAgent: generating weekly schedule for week %d.", week_number
        )
        return generate_text(prompt)

    def get_exam_preparation_tips(self, subject: str, exam_type: str = "written") -> str:
        """
        Return actionable exam preparation guidance.

        Args:
            subject:   Subject / topic name.
            exam_type: "written" | "MCQ" | "practical" | "oral".
        """
        prompt = f"""You are a Study Planner Agent and exam preparation expert.
Academic level: {_LEVEL}
Teaching style: {_STYLE}

Provide comprehensive exam preparation tips for:
- Subject: {subject}
- Exam type: {exam_type}

Include:
1. **Pre-Exam Preparation** (weeks before)
2. **Study Techniques** best suited to this exam type
3. **Common Mistakes** students make and how to avoid them
4. **Day-Before Strategy**
5. **Exam-Day Tips**
6. **Mental Health & Wellbeing** advice for exam stress

EXAM PREPARATION TIPS:"""
        logger.info(
            "PlannerAgent: generating exam prep tips for '%s'.", subject
        )
        return generate_text(prompt)

    def generate_revision_checklist(self, topics: list, subject: str = "") -> str:
        """
        Create a printable revision checklist.

        Args:
            topics:  List of topic strings to include.
            subject: Optional subject label.
        """
        topics_str = "\n".join(f"- {t}" for t in topics) if topics else "- All topics"
        subject_line = f"Subject: {subject}\n" if subject else ""
        prompt = f"""You are a Study Planner Agent.
{subject_line}
Create a detailed revision checklist for the following topics:
{topics_str}

For each topic include:
☐ Topic name
  ☐ Sub-topic 1
  ☐ Sub-topic 2
  ☐ Practice questions done
  ☐ Notes reviewed
  ☐ Confidence level: Low / Medium / High

Format as a printable checklist students can tick off.

REVISION CHECKLIST:"""
        logger.info("PlannerAgent: generating revision checklist.")
        return generate_text(prompt)
