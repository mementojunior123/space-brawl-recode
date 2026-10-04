const data = "`{DATA}`"
const network_key = "`{NETWORK_KEY}`"
window.dispatchEvent(new CustomEvent("NetworkSendData", {"detail" : {'data' : data, 'net_key' : network_key}}));