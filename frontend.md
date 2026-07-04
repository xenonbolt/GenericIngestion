# Frontend UI Requirements & API Specification

This document outlines the required features, UI components, and API integrations for building the frontend of the **Enterprise Agentic Intelligence Platform**. The current prototype is built with React and TypeScript, but these specifications apply regardless of the framework used (Next.js, Vue, etc.).

## 1. Authentication, Session & RBAC
The platform implements Role-Based Access Control (RBAC) separating `admin` and `basic` users.

- **Login / Signup Screen:** A full-screen UI that prompts the user for a **Username** and **Password**. It must have a toggle to switch between Login and Signup modes.
- **Session State:** The frontend must maintain the user's `username`, `role` (`admin` or `basic`), and a generated `sessionId` (e.g., `session-${Date.now()}`).
- **Persistence:** Save this JSON object to the browser's `localStorage` (key: `agentic_user`).
- **Logout:** A logout button in the main app should clear `localStorage` and return the user to the login screen.
- **API Endpoints:**
  - `POST /auth/signup` - Body: `{"username": "...", "password": "..."}`
  - `POST /auth/login` - Body: `{"username": "...", "password": "..."}`

## 2. Core Layout & Role-Based Views
The main dashboard should feature a clean, enterprise-grade interface divided into functional areas:
1. **Top Navigation/Header:** Displays the logged-in user's name, a "Logout" button, and an "Upload Knowledge" action button.
   - *If `role === 'admin'`*, a special "Admin Dashboard" button should also be visible.
2. **Chat Interface (Left Panel):** A conversational UI for interacting with the AI.
3. **Live Agent Trace (Right Panel):** A visual flowchart that draws itself in real-time as the multi-agent backend thinks.

---

## 3. Component Details & API Specs

### A. The Chat Interface
- **Message List:** Scrollable container showing user messages and assistant responses.
- **Auto-scroll:** Must automatically scroll to the bottom when a new message arrives.
- **Typing Indicator:** Show an "Agent is thinking..." state while waiting for the API response.
- **API Endpoint:** 
  - `POST /chat`
  - Body: `{"user_id": "<from_localStorage>", "session_id": "<from_localStorage>", "message": "<user_input>"}`
  - Response: `{"reply": "..."}`

### B. Knowledge Ingestion (Upload Modal)
Triggered by the "Upload Knowledge" button.
- **File Input & Metadata:** Form fields for Category, Tags, and Summary. Supports an "Auto-Fill" magic button calling `POST /analyze-metadata`.
- **RBAC Upload Logic:** 
  - When a user submits, the `user_id` and `role` must be appended to the form data.
  - **API Endpoint:** `POST /upload` (multipart/form-data with `file`, `summary`, `category`, `tags`, `user_id`, `role`).
  - *If Admin:* The file is ingested instantly.
  - *If Basic User:* The backend returns `status: "pending"`. The frontend should show a toast saying "Upload submitted for Admin approval."

### C. Admin Dashboard (Admin Only)
A modal/page exclusively accessible to users with `role === 'admin'`. It contains three tabs:
1. **Pending Approvals Tab:**
   - Fetches a list of pending uploads from `GET /admin/approvals`.
   - Displays a table showing the filename, submitter username, and timestamp.
   - Provides "Approve" and "Reject" buttons for each file.
   - **API Endpoints:** `POST /admin/approvals/{id}/approve` and `POST /admin/approvals/{id}/reject`.
2. **User Management Tab:**
   - Fetches a list of all users from `GET /admin/users`.
   - Displays a list/table of usernames and their current roles.
   - Provides a dropdown menu for each user to toggle their role between `basic` and `admin`.
   - **API Endpoint:** `POST /admin/users/{username}/role` - Body: `{"role": "..."}`
3. **System Audit Logs Tab:**
   - Fetches system-wide activity logs from `GET /admin/audit-logs`.
   - Displays a read-only data grid showing Timestamp, User ID, Action, and Details.

### D. Live Agent Trace (Visual Flowchart)
- Connect to `ws://<backend_url>/ws/agent-stream`.
- Render a live visual graph using `reactflow` based on incoming JSON events detailing the active LangGraph node, its actions, and token optimization metrics.
