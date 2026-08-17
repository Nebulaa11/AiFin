Summary
This PR extends the AiFin MVP with authentication, a full dashboard UI, a free local finance chat agent (no OpenAI required), and richer optimizer/analyze APIs. Users can sign in, save their financial profile, explore strategies on a Khaata-inspired dashboard, and chat with an agent trained on finance intents.

What's included
Authentication & user data
Google OAuth sign-in with JWT session handling
Dev login fallback when Google OAuth is not configured (ALLOW_DEV_AUTH=true)
Persistent user financial profiles (GET/PUT)
Chat session and message history stored in the database
Frontend (React + Vite)
Login flow with Google Sign-In and local dev fallback
Dashboard with Assets, Debts, and Strategy tabs
Chart.js visualizations for projections and breakdowns
Floating chat widget with conversation history
Responsive, Khaata-inspired layout and styling
Backend services & APIs
Local finance agent — intent classification + profile-aware responses (no paid LLM required)
Enhanced /api/v1/analyze — goals, timeline, sensitivity, debt vs invest comparison, next actions, assumptions
New endpoints: /what-if, /chat, auth config, user profile routes
Finance engine, optimizer (4 strategies), simulator, emergency fund, goal planner, insights, timeline
Optional ML boost for strategy scoring (RandomForest) and chat intent model (TF-IDF + LogisticRegression)
Config & docs
.env.example files for root, backend, and frontend
Sample training data for strategy and chat intent models
Why this approach
Local agent first — keeps chat free and usable without API keys
Dev auth — easy local development without Google OAuth setup
Modular services — finance logic separated from API routes for easier testing and extension
Test plan
Start backend (uvicorn) and frontend (npm run dev)
Sign in via dev login (or Google OAuth if configured)
Save/update financial profile on dashboard
Run analysis on Assets/Debts/Strategy tabs and verify charts render
Open chat widget, send finance questions, confirm contextual replies and history persist after refresh
Call /api/v1/analyze and /what-if with sample payload and verify structured response
Confirm backend/.env is not committed (secrets stay local)
Notes for reviewers
Google OAuth requires GOOGLE_CLIENT_ID and JWT_SECRET in backend/.env (see .env.example)
OpenAI/LangChain integration remains optional; the default chat path uses the local agent
SQLite is used for local dev; profile and chat data persist in the local DB
