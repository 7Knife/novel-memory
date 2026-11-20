# Option A — local stdio

Already active in `cordis.patch.yml`:

```yaml
serverName: basicmemory
transport: stdio
command: uvx
args: ['--prerelease=allow', 'basic-memory', 'mcp']
```

# Option B — Basic Memory Cloud / streamable HTTP

Replace the `config` block with your actual endpoint. Do not paste API keys into this file.

```yaml
serverName: basicmemory
transport: streamable-http
url: https://<your-basic-memory-cloud-mcp-endpoint>/mcp
failOnStartupError: true
```

If your DSH profile already stores a credential, use a Loader `!!js` expression to reference it instead of embedding a secret.

# Install

```bash
dsh plugin --profile <profile> add D:\AI\Agent\DSH\Memory\novel-memory\dsh-mcp-bundle
```

Restart DSH, then verify a tool such as `mcp__basicmemory__bm_search` is available.

# Security

- Do not put `bmc_` API keys or JWTs in this repo.
- Use Basic Memory Cloud configuration on the machine (`basic-memory cloud api-key save`) and per-project cloud routing.
- The cloud MCP endpoint must be provided by your Basic Memory Cloud account; this template does not fabricate a URL.
