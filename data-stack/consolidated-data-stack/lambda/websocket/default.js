exports.handler = async (event) => {
  console.log('Default route:', JSON.stringify(event));
  return { statusCode: 200, body: 'Message received' };
};
