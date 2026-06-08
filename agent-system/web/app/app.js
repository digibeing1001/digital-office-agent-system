const state = {
  installPrompt: null
};

const byId = (id) => document.getElementById(id);

function log(message, data) {
  const output = byId("logOutput");
  const stamp = new Date().toISOString();
  const details = data ? `\n${JSON.stringify(data, null, 2)}` : "";
  output.textContent = `[${stamp}] ${message}${details}`;
  byId("updatedAt").textContent = stamp;
}

async function getJson(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || data.status || `Request failed: ${response.status}`);
  }
  return data;
}

function renderWorkflows(workflows) {
  const list = byId("workflowList");
  const recent = workflows?.recent || [];
  byId("workflowMeta").textContent = `${workflows?.active_count || 0} active, ${workflows?.draft_revision_count || 0} drafts`;
  if (!recent.length) {
    list.className = "list empty";
    list.textContent = "No workflows yet.";
    return;
  }
  list.className = "list";
  list.replaceChildren(...recent.map((workflow) => {
    const item = document.createElement("div");
    item.className = "item";
    const title = document.createElement("strong");
    title.textContent = workflow.title || workflow.run_id || "Untitled workflow";
    const meta = document.createElement("span");
    meta.textContent = `${workflow.status || "unknown"} / ${workflow.agent_id || "unassigned"} / ${workflow.project_id || "no project"}`;
    item.append(title, meta);
    return item;
  }));
}

async function refresh() {
  byId("healthStatus").textContent = "Checking";
  try {
    const [health, gui] = await Promise.all([
      getJson("/api/health"),
      getJson("/api/gui-state?limit=8")
    ]);
    byId("healthStatus").textContent = health.status;
    byId("healthStatus").className = health.status === "ok" ? "" : "bad";
    byId("workflowCount").textContent = gui.workflows?.count ?? 0;
    byId("taskCount").textContent = gui.tasks?.count ?? 0;
    byId("approvalCount").textContent = gui.approvals?.count ?? 0;
    renderWorkflows(gui.workflows);
    log("Web UI shell connected.", { health: health.status, capabilities: gui.capabilities?.map((item) => item.id) || [] });
  } catch (error) {
    byId("healthStatus").textContent = "offline";
    byId("healthStatus").className = "bad";
    log(error.message || "Connection failed.");
  }
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  state.installPrompt = event;
  byId("installButton").hidden = false;
});

byId("installButton").addEventListener("click", async () => {
  if (!state.installPrompt) {
    return;
  }
  state.installPrompt.prompt();
  await state.installPrompt.userChoice;
  state.installPrompt = null;
  byId("installButton").hidden = true;
});

byId("refreshButton").addEventListener("click", refresh);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js").catch((error) => {
    log("Service worker registration failed.", { error: error.message });
  });
}

refresh();
