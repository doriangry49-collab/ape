# Developer Ecosystem — Plugin & Agent Authoring Guide

Welcome to the **APE v1.0 Developer Ecosystem**. This guide allows 3rd-party developers to author and publish custom plugins and specialized agents in under 10 minutes.

---

## 🚀 1. Creating a Custom APE Plugin

Every APE plugin implements the `ApePlugin` protocol interface:

```python
from ape.plugins import ApePlugin, PluginManifest

class MyCustomPlugin:
    name = "my_custom_plugin"
    version = "1.0.0"
    api_version = "1"

    def register(self, registry) -> None:
        # Register custom validators, policy rules, or runtime packs
        pass
```

---

## 🤖 2. Creating a Specialized Fabric Agent

Specialized agents implement the `ApeAgent` protocol interface:

```python
from ape.fabric import ApeAgent, AgentReport

class CustomSecurityAgent:
    name = "custom_security_agent"
    role = "security"

    def execute(self, workspace_context) -> AgentReport:
        return AgentReport(
            agent_name=self.name,
            role=self.role,
            status="COMPLETED",
            findings=["Scanned code dependencies: Zero vulnerabilities found."],
        )
```

---

## 📦 3. Publishing to Marketplace

Publish your signed package using the APE CLI:

```bash
ape factory generate security --desc "Custom Security Auditor Agent"
```
