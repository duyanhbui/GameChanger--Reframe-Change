# Change Management Assessment Tool

## Overview
A Flask-based change management platform for assessing stakeholder sentiment, generating AI-powered strategies, and managing organizational change concerns. Features role-based access control, company management, and automated communication scheduling.

## Architecture
- **Backend**: Flask with SQLAlchemy (PostgreSQL/SQLite), Flask-Login for auth
- **Frontend**: Jinja2 templates with Bootstrap 5, Chart.js, Feather Icons
- **AI**: OpenAI GPT-4o for strategy generation and response suggestions
- **Auth**: Flask-Login with role-based access (Admin / Change Manager)

## Key Files
- `main.py` - Main application with routes, models, and business logic
- `departments.py` - Centralized department list used across the app
- `strategy_generator.py` - AI strategy generation from meeting transcriptions
- `ai_response_service.py` - AI-powered concern response suggestions
- `email_service.py` - Email notification service (SendGrid)
- `mental_models.py` - KB16 mental model definitions and mapping logic

## Database Models (in main.py)
- `User` - User accounts with roles (admin, change_manager) and Flask-Login integration
- `Company` - Company entities with projects and user access assignments
- `UserCompanyAccess` - Many-to-many mapping of users to companies
- `ChangeProject` - Project metadata, strategy components, file uploads, dates; linked to Company
- `StakeholderResponse` - Individual survey responses with mental model assignment
- `ConcernAssignment` - Concern tracking and SME assignment workflow
- `FAQEntry` - Project-specific FAQ entries
- `CommunicationSchedule` - Automated pulse check scheduling (fortnightly/key_phases/minimal)
- `CommunicationLog` - Log of sent communications

## Authentication & Roles
- **Admin**: Full access to all features, can create/manage users, companies, and assignments
- **Change Manager**: Access limited to assigned companies and their projects
- First signup creates an admin account; subsequent users are created by admins
- Routes: `/login`, `/signup`, `/logout`
- Admin routes: `/admin/users`, `/admin/companies` (with create/edit/toggle)

## Key Routes
- `/` - Stakeholder survey form (public, accepts `project_id` query param)
- `/submit` - Process survey submission (public)
- `/manager` - Dashboard with analytics (auth required)
- `/manager/projects` - Project listing with company column
- `/manager/projects/create` - Create project with company assignment
- `/manager/projects/<id>/edit` - Edit project
- `/manager/concerns` - Concern management with search/filter (by name, department, date range)
- `/manager/communications` - Communication center
- `/manager/communications/schedules` - Manage automated pulse check schedules
- `/api/projects/search` - Searchable project filter API (supports q, status, company_id params)

## Project-Scoped Navigation
The active project is stored in the Flask session via `get_active_project()` / `get_active_project_id()` helpers. When a project is selected (via URL param or searchable filter), it persists in the session across all manager pages. The `/manager/clear-project` route clears the session-stored project filter.

## Searchable Project Filter
All manager pages include a reusable searchable project filter (`project_filter.html`) that supports:
- Text search for project names
- Filter by status (active/inactive/all)
- Filter by company
- Results from `/api/projects/search` API with access control

## Communication Scheduling
- Supports three frequencies: fortnightly (2 weeks), key_phases (~monthly), minimal (~2 months)
- Schedules can be created, paused/resumed, and triggered manually
- Communication logs track sent emails with recipient counts

## File Uploads
- Supported formats: PDF, DOC, DOCX, TXT
- Files stored in `uploads/` directory with timestamped unique names
- Strategy components each support both file upload and text input

## Navigation
All manager pages include a persistent navigation bar (`nav_bar.html`) with links to Dashboard, Projects, Concerns, Communications, Schedules, and Admin (for admin users). User profile dropdown shows current user info and logout option.
