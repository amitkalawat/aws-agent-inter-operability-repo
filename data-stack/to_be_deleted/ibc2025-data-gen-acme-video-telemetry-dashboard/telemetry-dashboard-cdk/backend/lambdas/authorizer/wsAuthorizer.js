const https = require('https');
const jose = require('node-jose');

// Cache for JWKS
let jwksCache = null;
let jwksCacheExpiry = 0;

exports.handler = async (event) => {
  console.log('Authorizer event:', JSON.stringify(event));
  
  try {
    // Extract token from query parameters
    const token = event.queryStringParameters?.token;
    
    if (!token) {
      console.log('No token provided');
      return generatePolicy('user', 'Deny', event.methodArn);
    }
    
    // Verify the Cognito JWT token
    const decoded = await verifyToken(token);
    
    if (decoded) {
      console.log('Token verified for user:', decoded['cognito:username']);
      return generatePolicy(decoded['cognito:username'], 'Allow', event.methodArn, {
        userId: decoded['cognito:username'],
        email: decoded.email
      });
    } else {
      console.log('Token verification failed');
      return generatePolicy('user', 'Deny', event.methodArn);
    }
  } catch (error) {
    console.error('Authorizer error:', error);
    return generatePolicy('user', 'Deny', event.methodArn);
  }
};

async function verifyToken(token) {
  try {
    // Decode token header to get kid
    const sections = token.split('.');
    if (sections.length !== 3) {
      throw new Error('Invalid token format');
    }
    
    const header = JSON.parse(Buffer.from(sections[0], 'base64').toString('utf8'));
    const kid = header.kid;
    
    // Get JWKS
    const jwks = await getJWKS();
    
    // Find the key
    const key = jwks.keys.find(k => k.kid === kid);
    if (!key) {
      throw new Error('Key not found');
    }
    
    // Verify the token
    const result = await jose.JWK.asKey(key);
    const verified = await jose.JWS.createVerify(result).verify(token);
    const claims = JSON.parse(verified.payload.toString());
    
    // Check expiration
    const now = Math.floor(Date.now() / 1000);
    if (claims.exp < now) {
      throw new Error('Token expired');
    }
    
    // Check token use
    if (claims.token_use !== 'id' && claims.token_use !== 'access') {
      throw new Error('Invalid token use');
    }
    
    return claims;
  } catch (error) {
    console.error('Token verification error:', error);
    return null;
  }
}

async function getJWKS() {
  // Check cache
  const now = Date.now();
  if (jwksCache && jwksCacheExpiry > now) {
    return jwksCache;
  }
  
  // Fetch JWKS
  const region = process.env.REGION || 'us-east-1';
  const userPoolId = process.env.USER_POOL_ID;
  const url = `https://cognito-idp.${region}.amazonaws.com/${userPoolId}/.well-known/jwks.json`;
  
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          jwksCache = JSON.parse(data);
          jwksCacheExpiry = now + (60 * 60 * 1000); // Cache for 1 hour
          resolve(jwksCache);
        } catch (error) {
          reject(error);
        }
      });
    }).on('error', reject);
  });
}

function generatePolicy(principalId, effect, resource, context = {}) {
  const authResponse = {
    principalId
  };
  
  if (effect && resource) {
    authResponse.policyDocument = {
      Version: '2012-10-17',
      Statement: [
        {
          Action: 'execute-api:Invoke',
          Effect: effect,
          Resource: resource
        }
      ]
    };
  }
  
  if (context) {
    authResponse.context = context;
  }
  
  return authResponse;
}