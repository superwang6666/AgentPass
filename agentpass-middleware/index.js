/**
 * AgentPass Middleware for Express
 * Minimal machine-to-machine login standard
 */

/**
 * Create AgentPass middleware gate
 * @param {Object} options - Configuration options
 * @param {number} options.maxBodySize - Maximum request body size in bytes (default: 1MB)
 * @param {string} options.endpoint - Custom endpoint path (default: /api/agent/entry)
 * @returns {Function} Express middleware
 */
function gate(options = {}) {
  const maxBodySize = options.maxBodySize || 1 * 1024 * 1024; // 1MB default
  const endpoint = options.endpoint || '/api/agent/entry';
  
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

    // Only process configured endpoint requests
    if (req.path !== endpoint || req.method !== 'POST') {
      return next();
    }

    // Parse and validate request body with size limit
    let body = '';
    let bodySize = 0;
    
    req.on('data', chunk => {
      bodySize += chunk.length;
      
      // Check size limit
      if (bodySize > maxBodySize) {
        req.destroy();
        return res.status(413).json({
          error: 'Payload too large',
          message: `Request body exceeds ${maxBodySize} bytes limit`
        });
      }
      
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
