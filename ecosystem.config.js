module.exports = {
  apps: [
    {
      name: "orch-backend",
      namespace: "orchestrator",
      script: "python3",
      args: "-m backend.main",
      cwd: "/home/spiritai/orchestrator/targeting_sys",
      autorestart: true,
      env: {
        PYTHONPATH: ".",
      },
    },
    {
      name: "orch-frontend",
      namespace: "orchestrator",
      cwd: "/home/spiritai/orchestrator/targeting_sys/frontend",
      script: "npm",
      args: "run preview",
      autorestart: true,
    },
  ],
};
