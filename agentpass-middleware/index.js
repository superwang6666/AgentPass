/**
 * AgentPass Middleware for Express
 * Minimal machine-to-machine login standard
 */

/**
 * Create AgentPass middleware gate
 * @returns {Function} Express middleware
 */
function gate() {
  return (req, res, next) => {
    // Initialize agentContext on request
    req.agentContext = {};

    // Attach cleanup on response finish
    res.on('finish', () => {
      // Destroy credentials from context
      if (req.agentContext && req.agentContext.api_key) {
        delete req.agentContext.api_key;
        req.agentContext = null;
      }
    });

    // Only process /api/agent/entry requests
    if (req.path !== '/api/agent/entry' || req.method !== 'POST') {
      return next();
    }

    // Parse and validate request body
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', () => {
      try {
        const payload = JSON.parse(body);

        // Validate auth_type is BYOK
        if (payload.auth_type !== 'BYOK') {
          return res.status(400).json({
            error: 'Invalid auth_type. Only BYOK is supported.'
          });
        }

        // Validate credentials structure
        if (!payload.credentials || !payload.credentials.api_key) {
          return res.status(400).json({
            error: 'Missing credentials.api_key'
          });
        }

        // Inject API key into request context
        req.agentContext.api_key = payload.credentials.api_key;
        req.agentContext.provider = payload.credentials.provider || 'openai';
        req.agentContext.identity = payload.identity;
        req.agentContext.task = payload.task;

        // Continue to next middleware
        next();
      } catch (err) {
        res.status(400).json({
          error: 'Invalid JSON in request body'
        });
      }
    });
  };
}

/**
 * Helper to use the API key in requests
 * @param {string} key - The API key from agentContext
 * @returns {Object} Headers for API request
 */
function createHeaders(key) {
  return {
    'Authorization': `Bearer ${key}`,
    'Content-Type': 'application/json'
  };
}

module.exports = {
  gate,
  createHeaders
};
