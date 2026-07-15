Secrets handling

- Never commit `.env` or any file that contains secrets. Keep them local or in a secret manager.
- Recommended local workflow:
  1. Create `.env` from `.env.example`.
  2. Add `OPENAI_API_KEY=sk-...` to `.env`.
  3. Start the app in the same shell so the environment is loaded by `python-dotenv`.
- For production, prefer an environment secrets manager (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault) and inject the value into the runtime environment rather than storing a file on disk.

Logging

- Do not log secrets. Ensure structured logs redact `OPENAI_API_KEY` and similar fields.

Rotation

- Have a plan to rotate API keys and update deployments without downtime.
