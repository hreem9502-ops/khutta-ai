# Khutta (خطتي): Academic Registration Assistant

A web app that suggests a student's courses for the next term from their transcript and their department's study plan.

The design rule: **fixed rules decide what a student may register for; the AI only chooses among those courses and explains why.** An AI answer can never add an ineligible course, because every answer is re-checked in code before it is shown.

## How it works

1. **Upload.** The student picks a department and term and uploads the transcript PDF. The backend reads the text (`pdfplumber`) and matches course codes against the study plan.
2. **Review.** The student confirms or corrects which courses are passed, in progress, or not taken. Reading a PDF is never trusted blindly.
3. **Eligibility (code).** `prerequisite_checker.py` removes courses already taken, courses not offered this term, and courses with unmet prerequisites. It also works out the credit-hour limits from the GPA and the remaining elective hours.
4. **Advice (AI).** Gemini picks and ranks courses from the eligible list only and writes a short reason in Arabic and English for each. Only course codes, grades and the GPA are sent; no name or student ID is ever extracted.
5. **Validation (code).** `recommender.py` drops unknown, ineligible or duplicate picks, enforces corequisites and the maximum load, and tops up to the minimum load. If the AI is unavailable or its answer is unusable, a rule-based advisor produces the schedule and the UI says so.

```
backend/app
  models/      Pydantic schemas (study plan, transcript, recommendation)
  services/    pdf_parser, transcript_analyzer, prerequisite_checker,
               rule_advisor, ai_advisor, recommender, plan_repository
  routers/     courses (departments, plans), upload (parse), suggest
  data/plans/  Study plans as JSON, one file per department
frontend/src
  app/[locale] Pages: home, upload, review, results, plan, about
  components/  layout, ui, and one folder per feature
  hooks/       usePlanner, useApiResource, useStudyPlan, ...
  lib/         API client, planner state, constants
messages/      ar.json, en.json
```

## Run it

Backend (Python 3.11+):

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt   # Windows; use .venv/bin/pip on macOS/Linux
cp .env.example .env                                  # add GEMINI_API_KEY to enable the AI advisor
.venv/Scripts/python -m uvicorn app.main:app --port 8000
.venv/Scripts/python -m pytest
```

Without `GEMINI_API_KEY` the app still works, using the rule-based advisor.

Frontend (Node 20+, pnpm):

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:3000, expects the API on http://localhost:8000
```

Set `NEXT_PUBLIC_API_URL` if the API runs elsewhere.

## Before real use

- **Replace the sample study plans.** `backend/app/data/plans/*.json` contain illustrative plans (CS and Networks), not the college's real ones. The rules block (min/max hours, GPA tiers) and each course's `terms` are placeholders too.
- **Tune the transcript parser against a real transcript.** It expects one course per line with the code, then the credit hours, then the grade (for example `CS 101  Intro to Computing  3  A  4.00`). Arabic-only layouts, reversed text order and scanned PDFs need a sample to handle. The review step exists so misreads are caught.
- **The Gemini call is untested against the live API**, because no key was available during development. It is covered by tests with a fake client; try it once with a key and check the Arabic output.
