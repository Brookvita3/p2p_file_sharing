const os = require("os");

function getLocalIp() {
  const interfaces = os.networkInterfaces();
  for (let interfaceName in interfaces) {
    for (let i = 0; i < interfaces[interfaceName].length; i++) {
      const iface = interfaces[interfaceName][i];
      if (iface.family === "IPv4" && !iface.internal) {
        return iface.address; // Return the first non-internal IPv4 address
      }
    }
  }
  return null; // Return null if no valid IPv4 address found
}

const splitIntoChunks = (data, chunkSize) => {
  const chunks = [];
  let i = 0;
  while (i < data.length) {
    chunks.push(data.slice(i, i + chunkSize));
    i += chunkSize;
  }
  return chunks;
};

module.exports = {
  getLocalIp,
  splitIntoChunks,
};
