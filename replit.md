# Change Management Assessment Tool

## Overview
A Flask-based change management platform for assessing stakeholder sentiment, generating AI-powered strategies, and managing organizational change concerns.

## Architecture
- **Backend**: Flask with SQLAlchemy (SQLite)
- **Frontend**: Jinja2 templates with Bootstrap 5, Chart.js, Feather Icons
- **AI**: OpenAI GPT-4o for strategy generation and response suggestions

## Key Files
- `main.py` - Main application with routes, models, and business logic
- `departments.py` - Centralized department list used across the app (survey dropdown, etc.)
- `strategy_generator.py` - AI strategy generation from meeting transcriptions
- `ai_response_service.py` - AI-powered concern response suggestions
- `email_service.py` - Email notification service
- `mental_models.py` - KB16 mental model definitions and mapping logic

## Database Models (in main.py)
- `ChangeProject` - Project metadata, strategy components, file uploads, dates
- `StakeholderResponse` - Individual survey responses with mental model assignment
- `ConcernAssignment` - Concern tracking and SME assignment workflow
- `FAQEntry` - Project-specific FAQ entries

## Key Routes
- `/` - Stakeholder survey form (accepts `project_id` query param)
- `/submit` - Process survey submission
- `/manager` - Dashboard with analytics (accepts `project_id` for filtering)
- `/manager/projects` - Project listing
- `/manager/projects/create` - Create new project
- `/manager/projects/<id>/edit` - Edit existing project
- `/manager/concerns` - Concern management (accepts `project_id`)
- `/manager/communications` - Communication center (accepts `project_id`)

## Project-Scoped Navigation
The active project is stored in the Flask session via `get_active_project()` / `get_active_project_id()` helpers. When a project is selected (via URL param or dropdown), it persists in the session across Dashboard, Concerns, Communications, FAQ, and Export pages. The `/manager/clear-project` route clears the session-stored project filter.

## File Uploads
- Supported formats: PDF, DOC, DOCX, TXT
- Files stored in `uploads/` directory with timestamped unique names
- Strategy components each support both file upload and text input
