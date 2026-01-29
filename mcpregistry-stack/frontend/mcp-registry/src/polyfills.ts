// Polyfills for amazon-cognito-identity-js in browser
if (typeof global === 'undefined') {
  (window as any).global = window;
}
