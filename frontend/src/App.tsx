import { useEffect, useMemo, useState } from "react";
import {
  fetchProjectMeta,
  fetchStateSummary,
  fetchGatewayProviders,
  fetchGatewayRouters,
  fetchGatewayStatus,
  resetState,
  runAllQueries,
  runCustomChat,
  runSingleQuery,
} from "./api";
import type { GatewayProviders, GatewayRouters, GatewayStatus, ProjectMeta, RunResponse, StateSummary } from "./types";
import "./App.css";

type TabKey = "overview" | "runner" | "traces" | "memory" | "validation" | "ops";

const TABS: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "runner", label: "Live Runner" },
  { key: "traces", label: "Trace Viewer" },
  { key: "memory", label: "Memory" },
  { key: "validation", label: "Validation" },
  { key: "ops", label: "Ops" },
];

const QUERY_IDS = ["A", "B", "C_WRITE", "C_READ", "D"];

function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [projectMeta, setProjectMeta] = useState<ProjectMeta | null>(null);
  const [stateSummary, setStateSummary] = useState<StateSummary | null>(null);
  const [runResponse, setRunResponse] = useState<RunResponse | null>(null);
  const [selectedTraceQuery, setSelectedTraceQuery] = useState<string>("");
  const [selectedQuery, setSelectedQuery] = useState<string>("A");
  const [customQuery, setCustomQuery] = useState<string>("What is the capital of France?");
  const [customMaxIterations, setCustomMaxIterations] = useState<number>(4);
  const [cleanStateBeforeRun, setCleanStateBeforeRun] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  const [gatewayProviders, setGatewayProviders] = useState<GatewayProviders | null>(null);
  const [gatewayStatus, setGatewayStatus] = useState<GatewayStatus | null>(null);
  const [gatewayRouters, setGatewayRouters] = useState<GatewayRouters | null>(null);

  const selectedRun = useMemo(() => {
    if (!runResponse) {
      return null;
    }
    return runResponse.results.find((item) => item.query_id === selectedTraceQuery) ?? runResponse.results[0] ?? null;
  }, [runResponse, selectedTraceQuery]);

  async function bootstrap() {
    setLoading(true);
    setError("");
    try {
      const [meta, state, providers, status, routers] = await Promise.all([
        fetchProjectMeta(),
        fetchStateSummary(),
        fetchGatewayProviders(),
        fetchGatewayStatus(),
        fetchGatewayRouters(),
      ]);
      setProjectMeta(meta);
      setStateSummary(state);
      setGatewayProviders(providers);
      setGatewayStatus(status);
      setGatewayRouters(routers);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void bootstrap();
  }, []);

  async function handleRunQuery() {
    setRunning(true);
    setError("");
    try {
      const response = await runSingleQuery(selectedQuery, cleanStateBeforeRun);
      setRunResponse(response);
      setSelectedTraceQuery(response.results[0]?.query_id ?? "");
      setStateSummary(await fetchStateSummary());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run query.");
    } finally {
      setRunning(false);
    }
  }

  async function handleRunCustomChat() {
    setRunning(true);
    setError("");
    try {
      const response = await runCustomChat(customQuery, customMaxIterations, cleanStateBeforeRun);
      setRunResponse(response);
      setSelectedTraceQuery(response.results[0]?.query_id ?? "");
      setStateSummary(await fetchStateSummary());
      setActiveTab("traces");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run custom query.");
    } finally {
      setRunning(false);
    }
  }

  async function handleRunAll() {
    setRunning(true);
    setError("");
    try {
      const response = await runAllQueries(cleanStateBeforeRun);
      setRunResponse(response);
      setSelectedTraceQuery(response.results[0]?.query_id ?? "");
      setStateSummary(await fetchStateSummary());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run all queries.");
    } finally {
      setRunning(false);
    }
  }

  async function handleResetState() {
    setRunning(true);
    setError("");
    try {
      await resetState();
      setStateSummary(await fetchStateSummary());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset state.");
    } finally {
      setRunning(false);
    }
  }

  async function handleRefreshOps() {
    setError("");
    try {
      const [providers, status, routers] = await Promise.all([
        fetchGatewayProviders(),
        fetchGatewayStatus(),
        fetchGatewayRouters(),
      ]);
      setGatewayProviders(providers);
      setGatewayStatus(status);
      setGatewayRouters(routers);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh gateway status.");
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>Session6 YouTube Demo</h1>
          <p>Live architecture walkthrough, typed traces, memory persistence, and validation evidence.</p>
        </div>
      </header>

      <nav className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={tab.key === activeTab ? "tab active" : "tab"}
            onClick={() => setActiveTab(tab.key)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <div className="panel">Loading demo data...</div> : null}

      {!loading && activeTab === "overview" && projectMeta ? (
        <section className="panel">
          <h2>{projectMeta.title}</h2>
          <p>{projectMeta.summary}</p>
          <div className="grid two">
            <div>
              <h3>Modules</h3>
              {projectMeta.modules.map((module) => (
                <div className="item" key={module.path}>
                  <strong>{module.name}</strong>
                  <code>{module.path}</code>
                  <span>{module.role}</span>
                </div>
              ))}
            </div>
            <div>
              <h3>Constraints</h3>
              <ul>
                {projectMeta.constraints.map((constraint) => (
                  <li key={constraint}>{constraint}</li>
                ))}
              </ul>
              <h3>Run Commands</h3>
              <ul>
                {projectMeta.commands.map((command) => (
                  <li key={command}>
                    <code>{command}</code>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      ) : null}

      {!loading && activeTab === "runner" ? (
        <section className="panel">
          <h2>Live Runner</h2>
          <h3>Custom live query</h3>
          <label className="full-width">
            Type any question
            <textarea
              rows={3}
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              placeholder="e.g. Remember my favorite color is blue"
            />
          </label>
          <div className="row">
            <label>
              Max iterations
              <input
                type="number"
                min={1}
                max={16}
                value={customMaxIterations}
                onChange={(e) => setCustomMaxIterations(Number(e.target.value))}
              />
            </label>
            <button type="button" onClick={handleRunCustomChat} disabled={running || !customQuery.trim()}>
              {running ? "Running..." : "Run Custom Query"}
            </button>
          </div>

          <h3>Assignment target queries</h3>
          <div className="row">
            <label>
              Query
              <select value={selectedQuery} onChange={(e) => setSelectedQuery(e.target.value)}>
                {QUERY_IDS.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={cleanStateBeforeRun}
                onChange={(e) => setCleanStateBeforeRun(e.target.checked)}
              />
              Clean state before run
            </label>
          </div>
          <div className="row">
            <button type="button" onClick={handleRunQuery} disabled={running}>
              {running ? "Running..." : "Run Selected Query"}
            </button>
            <button type="button" onClick={handleRunAll} disabled={running}>
              {running ? "Running..." : "Run Full Suite"}
            </button>
            <button type="button" onClick={handleResetState} disabled={running}>
              Reset Memory State
            </button>
          </div>
          {runResponse ? (
            <div className="result-block">
              <p>
                <strong>Overall pass:</strong> {String(runResponse.overall_pass)}
              </p>
              <p>
                <strong>Run at:</strong> {new Date(runResponse.ran_at).toLocaleString()}
              </p>
            </div>
          ) : null}
        </section>
      ) : null}

      {!loading && activeTab === "traces" ? (
        <section className="panel">
          <h2>Trace Viewer</h2>
          {!runResponse ? <p>Run a query first to inspect traces.</p> : null}
          {runResponse ? (
            <>
              <label>
                Query trace
                <select value={selectedTraceQuery} onChange={(e) => setSelectedTraceQuery(e.target.value)}>
                  {runResponse.results.map((result) => (
                    <option key={result.query_id} value={result.query_id}>
                      {result.query_id}
                    </option>
                  ))}
                </select>
              </label>
              <pre className="json-view">{JSON.stringify(selectedRun, null, 2)}</pre>
            </>
          ) : null}
        </section>
      ) : null}

      {!loading && activeTab === "memory" ? (
        <section className="panel">
          <h2>Memory Panel</h2>
          <p>
            <strong>Record count:</strong> {stateSummary?.record_count ?? 0}
          </p>
          <p>
            <strong>Last updated:</strong>{" "}
            {stateSummary?.last_updated ? new Date(stateSummary.last_updated).toLocaleString() : "N/A"}
          </p>
          <pre className="json-view">{JSON.stringify(stateSummary?.records ?? [], null, 2)}</pre>
        </section>
      ) : null}

      {!loading && activeTab === "validation" ? (
        <section className="panel">
          <h2>Validation Panel</h2>
          {!runResponse ? <p>Run queries to populate validation evidence.</p> : null}
          {runResponse ? (
            <table>
              <thead>
                <tr>
                  <th>Query</th>
                  <th>Iterations</th>
                  <th>Max Allowed</th>
                  <th>Passed</th>
                  <th>Answer</th>
                </tr>
              </thead>
              <tbody>
                {runResponse.results.map((result) => (
                  <tr key={result.query_id}>
                    <td>{result.query_id}</td>
                    <td>{result.iterations}</td>
                    <td>{result.max_allowed_iterations}</td>
                    <td>{String(result.passed)}</td>
                    <td>{result.answer}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </section>
      ) : null}

      {!loading && activeTab === "ops" ? (
        <section className="panel">
          <h2>Ops Panel</h2>
          <div className="row">
            <button type="button" onClick={handleRefreshOps}>
              Refresh Gateway Status
            </button>
          </div>
          <div className="grid three">
            <div>
              <h3>/v1/providers</h3>
              <pre className="json-view small">{JSON.stringify(gatewayProviders, null, 2)}</pre>
            </div>
            <div>
              <h3>/v1/status</h3>
              <pre className="json-view small">{JSON.stringify(gatewayStatus, null, 2)}</pre>
            </div>
            <div>
              <h3>/v1/routers</h3>
              <pre className="json-view small">{JSON.stringify(gatewayRouters, null, 2)}</pre>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}

export default App;
