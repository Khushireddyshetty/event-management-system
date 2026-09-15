# Deployment Notes

This ZIP is optimized for local Windows/VS Code execution. For a real deployment:

1. Set a strong `SECRET_KEY`, explicit `CORS_ORIGINS`, and any provider secrets through the deployment secret manager.
2. Set `FLASK_DEBUG=false`.
3. Use a production WSGI server (Waitress on Windows, or Gunicorn on Linux).
4. Build the frontend with `npm run build` and serve `frontend/dist` through a web server or static hosting.
5. Reverse proxy `/api` to the Flask service.
6. Keep `backend/database/events.db` on persistent storage and schedule backups.
7. Add authentication and authorization before exposing attendee, sponsor, or incident data outside a trusted network.
8. Monitor API logs and database disk usage.

The optional Gemini and SMTP integrations are non-blocking. If either is unavailable, core event management and local intelligence continue to work.