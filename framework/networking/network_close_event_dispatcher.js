const network_key = "`{NETWORK_KEY}`"
window.dispatchEvent(new CustomEvent("NetworkClose", {"detail" : {'net_key' : network_key}}));