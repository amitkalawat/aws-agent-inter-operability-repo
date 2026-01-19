#!/usr/bin/env python3
"""
Debug JWT token claims to understand aud values
"""
import jwt
import json
import requests

def decode_jwt_without_verification(token):
    """Decode JWT without signature verification to inspect claims"""
    try:
        # Decode without verification (just to see the payload)
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        return {"error": str(e)}

def get_cognito_jwks():
    """Get Cognito JWKS for token verification"""
    user_pool_id = "eu-central-1_CF2vh6s7M"
    region = "eu-central-1"
    
    jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("JWT Token Claims Debugger")
    print("=" * 40)
    
    # Get JWKS info
    print("Fetching Cognito JWKS...")
    jwks = get_cognito_jwks()
    if "error" not in jwks:
        print("✅ JWKS retrieved successfully")
        print(f"Keys available: {len(jwks.get('keys', []))}")
    else:
        print(f"❌ JWKS error: {jwks['error']}")
    
    print("\nPaste an access token to analyze its claims:")
    print("(Token will be decoded without signature verification)")
    print("Press Ctrl+C to exit\n")
    
    try:
        token = input("Access Token: ").strip()
        
        if token:
            print("\nDecoding token...")
            claims = decode_jwt_without_verification(token)
            
            print("\nToken Claims:")
            print(json.dumps(claims, indent=2, default=str))
            
            # Check specific claims
            if "error" not in claims:
                print(f"\n🔍 Key Claims Analysis:")
                print(f"   aud: {claims.get('aud', 'NOT_FOUND')}")
                print(f"   client_id: {claims.get('client_id', 'NOT_FOUND')}")
                print(f"   token_use: {claims.get('token_use', 'NOT_FOUND')}")
                print(f"   iss: {claims.get('iss', 'NOT_FOUND')}")
                
                # Determine what should be in allowedAudience
                if claims.get('token_use') == 'access':
                    print(f"\n💡 For access tokens, the allowedAudience should likely include:")
                    if claims.get('aud'):
                        print(f"   - {claims.get('aud')} (from aud claim)")
                    if claims.get('client_id'):
                        print(f"   - {claims.get('client_id')} (from client_id claim)")
                elif claims.get('token_use') == 'id':
                    print(f"\n💡 For ID tokens, the allowedAudience should include:")
                    print(f"   - {claims.get('aud')} (from aud claim)")
    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")