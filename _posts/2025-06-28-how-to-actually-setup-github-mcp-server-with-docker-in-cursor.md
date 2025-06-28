---
title: "How to Actually Setup GitHub MCP Server with Docker in Cursor (The Working Guide)"
date: 2025-06-28 11:45:28 +0200
tags: [cursor, github, mcp, docker, ai, development, troubleshooting]
---

Because the official documentation doesn't work, and you're probably pulling your hair out right now

> **🤖 AI Disclosure**: This guide was written by Claude (Anthropic's AI assistant) based on real troubleshooting experience. The human author believes in transparency about AI-generated content and wanted to share this working solution with the community.

## The Problem Everyone's Having

If you're here, you've probably tried to set up the GitHub MCP server in Cursor following the [official documentation](https://docs.cursor.com/context/model-context-protocol#mcp-resources), only to be greeted with frustrating "authorization denied" errors. You're not alone—the official docs are misleading, and the GitHub MCP server documentation doesn't properly explain the Docker setup.

**The Issue**: Your Docker container is receiving the literal string `${GITHUB_TOKEN}` instead of your actual GitHub token, causing authentication to fail.

## Why The Official Docs Don't Work

The problem stems from mixing two different approaches for environment variables:

1. **Cursor's MCP `env` section** (which uses JSON)
2. **Docker's `-e` flags** (which expect shell-style environment passing)

When you use shell substitution syntax like `${GITHUB_TOKEN}` in JSON, it doesn't get resolved—Docker literally receives the string `"${GITHUB_TOKEN}"` as your token.

## What You've Probably Tried (And Why It Fails)

Following the official docs, you likely created something like this in your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e",
        "GITHUB_TOOLSETS",
        "ghcr.io/github/github-mcp-server:latest"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}",
        "GITHUB_TOOLSETS": "issues,pull_requests,repos"
      }
    }
  }
}
```

**This doesn't work because:**

- ❌ You're mixing Docker `-e` flags with MCP `env` section
- ❌ Shell substitution `${GITHUB_TOKEN}` doesn't resolve in JSON
- ❌ Docker receives the literal string `"${GITHUB_TOKEN}"` as your token

## The Solution That Actually Works

Here's the step-by-step guide to get this working properly:

### Step 1: Set Up Your GitHub Token

First, make sure you have a GitHub Personal Access Token. If you don't have one:

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate a new token with these scopes: `repo`, `issues`, `pull_requests`
3. Copy the token (starts with `github_pat_...`)

Most people already have `GITHUB_TOKEN` in their environment. The GitHub MCP server expects `GITHUB_PERSONAL_ACCESS_TOKEN`, so create an alias:

```bash
# For your current session
export GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN

# Make it permanent (add to your shell profile)
echo 'export GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN' >> ~/.zshrc
```

### Step 2: Create the Correct MCP Configuration

Create or edit `~/.cursor/mcp.json` with this **working** configuration:

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e",
        "GITHUB_TOOLSETS=issues,pull_requests,repos",
        "ghcr.io/github/github-mcp-server:latest"
      ]
    }
  }
}
```

### What Makes This Work

✅ **No MCP `env` section** - eliminates JSON variable substitution issues  
✅ **Pure Docker syntax** - uses `-e VARNAME` to pass environment variables from host  
✅ **Clean separation** - Docker handles environment passing, MCP handles execution  

### Step 3: Verify Your Setup

Check that everything is configured correctly:

```bash
# Verify your token is set (shows first 12 characters for security)
echo "GITHUB_TOKEN: $(echo $GITHUB_TOKEN | cut -c1-12)..."
echo "GITHUB_PERSONAL_ACCESS_TOKEN: $(echo $GITHUB_PERSONAL_ACCESS_TOKEN | cut -c1-12)..."
```

Both should show the same token prefix (e.g., `github_pat_1...`).

### Step 4: Restart and Test

1. **Restart Cursor** completely (not just reload)
2. **Check MCP Settings**: Go to Cursor Settings → MCP
3. **Verify the server is listed** and shows as available

## Why This Works (Technical Explanation)

The magic is in how Docker handles environment variables:

1. **`-e GITHUB_PERSONAL_ACCESS_TOKEN`** (without a value) tells Docker: *"Pass the environment variable with this name from the host"*
2. **Your shell environment** contains the actual token value
3. **Docker automatically** resolves and passes the real token to the container
4. **No JSON parsing issues** because we're not using shell substitution in JSON

## Testing Your Setup

Once everything is configured, test that it's working:

**In Cursor's chat/composer**, try asking something like:

- *"List the open issues in this repository"*
- *"Show me the README file"*
- *"Create a new issue for [something]"*

The Cursor Agent should automatically use the GitHub MCP tools to fulfill these requests.

### ✅ **Proof It Works**

Here's what successful usage looks like:

- ✅ **File Access**: Can retrieve any file from your repositories
- ✅ **Issue Management**: Can list, create, and update issues  
- ✅ **Repository Operations**: Can access branches, commits, and metadata
- ✅ **No Auth Errors**: No more "authorization denied" messages

## When Things Go Wrong (Troubleshooting)

### Still getting "authorization denied"?

**Step 1**: Double-check your environment variables

```bash
# This should show your token (first 20 chars)
echo $GITHUB_PERSONAL_ACCESS_TOKEN | cut -c1-20
```

**Step 2**: Verify token permissions  
Your GitHub token needs these scopes:

- ✅ `repo` (for repository access)
- ✅ `issues` (for issue management)  
- ✅ `pull_requests` (for PR management)

**Step 3**: Fresh restart  
Environment variable changes need a clean slate:

1. Close Cursor completely
2. Open a new terminal session  
3. Start Cursor from the new terminal

### Nuclear Option: Hardcode the Token

⚠️ **Only if you're desperate** and the above doesn't work, you can hardcode the token:

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i", 
        "--rm",
        "ghcr.io/github/github-mcp-server:latest"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "github_pat_your_actual_token_here",
        "GITHUB_TOOLSETS": "issues,pull_requests,repos"
      }
    }
  }
}
```

**⚠️ Security Warning**: This puts your token in plaintext. Only use for testing or in secure environments.
