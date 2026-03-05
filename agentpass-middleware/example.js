/**
 * Example Server using AgentPass Middleware
 * 
 * This example shows how a website can integrate AgentPass
 * to receive requests from AI agents with their own API keys
 */

const express = require('express');

// In production, use: const agentPass = require('agentpass-middleware');
const agentPass = require('./index.js');

const app = express();
const PORT = 3000;

// Serve the discovery document
app.get('/.well-known/ai-agent.json', (req, res) => {
  res.json({
    version: "1.0.0",
    endpoint: "/api/agent/entry",
    methods: ["BYOK"],
    metadata: {
      name: "Example AgentPass Service",
      description: "A sample service supporting AgentPass protocol"
    }
  });
});

// Apply AgentPass middleware to agent endpoints
app.use('/api/agent', agentPass.gate());

// Handle agent requests
app.post('/api/agent/entry', (req, res) => {
  try {
    const { api_key, provider, identity, task } = req.agentContext;
    
    console.log('========== AgentPass Request Received ==========');
    console.log('Agent Identity:', identity);
    console.log('Provider:', provider);
    console.log('Task:', task);
    console.log('API Key available:', !!api_key);
    console.log('API Key length:', api_key ? api_key.length : 0);
    console.log('==============================================');

    // Simulate processing with the agent's API key
    // In production, you would use this key to call the agent's LLM
    
    const result = {
      status: 'success',
      message: 'Task processed successfully',
      agent_identity: identity,
      task_action: task.action,
      processed_at: new Date().toISOString(),
      // Simulate result from calling the API key's LLM
      result: `Processed "${task.action}" with params: ${JSON.stringify(task.params)}`
    };

    res.json(result);
  } catch (err) {
    res.status(400).json({
      status: 'error',
      message: err.message
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`AgentPass example server running on http://localhost:${PORT}`);
  console.log(`Discovery endpoint: http://localhost:${PORT}/.well-known/ai-agent.json`);
  console.log(`Agent endpoint: http://localhost:${PORT}/api/agent/entry`);
});
