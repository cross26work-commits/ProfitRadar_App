import { defineRailway, github, project, service } from "railway/iac";

// Secret values and publication approvals are entered as sealed Railway
// variables after owner review; this graph never embeds credentials.
const repo = "cross26work-commits/ProfitRadar_App";
const branch = "arc/profit-radar-release-readiness";
const commitSha = "9099d9a4667670eb505157acd66f0c5841f2534a";

export default defineRailway((ctx) => {
  if (ctx.projectId !== "812c77be-b93b-4db6-9338-1bc43f415707" ||
      ctx.environment !== "production") {
    throw new Error("Unexpected Railway project or environment");
  }

  const frontend = service("frontend", {
    source: github(repo, { branch, commitSha, rootDirectory: "/frontend" }),
    build: { builder: "RAILPACK", buildCommand: "npm ci && npm run build" },
    deploy: {
      startCommand: "npm run start -- --hostname 0.0.0.0 --port $PORT",
      healthcheckPath: "/",
      restartPolicyType: "ON_FAILURE",
    },
    env: { RAILPACK_NODE_VERSION: "24.18.0", RAILPACK_PRUNE_DEPS: "true" },
  });
  const backend = service("backend", {
    source: github(repo, { branch, commitSha, rootDirectory: "/backend" }),
    build: { builder: "RAILPACK", buildCommand: "python -m pip install --no-cache-dir -r requirements.txt" },
    deploy: {
      startCommand: "python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT",
      healthcheckPath: "/ready",
      restartPolicyType: "ON_FAILURE",
    },
    env: { RAILPACK_PYTHON_VERSION: "3.13.14" },
  });
  const worker = service("worker", {
    source: github(repo, { branch, commitSha, rootDirectory: "/backend" }),
    build: { builder: "RAILPACK", buildCommand: "python -m pip install --no-cache-dir -r requirements.txt" },
    deploy: {
      startCommand: "python -m scripts.sync_worker",
      healthcheckPath: "/health",
      restartPolicyType: "ON_FAILURE",
    },
    env: { RAILPACK_PYTHON_VERSION: "3.13.14" },
  });

  return project(ctx.projectName, { resources: [frontend, backend, worker] });
});
