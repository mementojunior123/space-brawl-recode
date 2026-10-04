//import {Peer} from "https://esm.sh/peerjs@1.5.5?bundle-deps";

const peerId = "`{PEERID}`";
const is_host = `{IS_HOST}`;
const network_key = "`{NETWORK_KEY}`";
const debug_level = `{DEBUG_LEVEL}`;
const MESSAGE_ENDER = "~&|^";

const mod = import("https://esm.sh/peerjs@1.5.5?bundle-deps");
mod.then((module) => {
    const Peer = module.Peer;
    //peerjs --port 5000 --key peerjs --path /
    //This is for local testing when peerjs is down
    //my savior https://lightrun.com/answers/peers-peerjs-server-receives-candidate-message-from-client-but-never-responds-to-it
    class NetworkClient {
        static createPeer(id, callback=()=>{}){
            let peer = new Peer(id, {
                debug: debug_level,
                /*
                port: 5000,
                path: '/',
                host: 'localhost'
                */

            });
            peer.on('open', (ID)=>{
                console.log('My peer ID is: ' + ID);
                callback();
            });
            return peer;
        }
        
        constructor(is_host, the_id, message_handler = (data) => {console.log(`Received "${data}"`)}, 
        error_handler = (error) => {console.log(error)}, on_close = () => {}, on_dc = () => {}, on_connection = () => {}) {
            this.is_host = is_host;
            this.connection_id = the_id;
            this.is_connected = false;
            this.destroyed = false;
            this.last_ping = Date.now();
            if (is_host) {
                this.peer = NetworkClient.createPeer(the_id, () => {
                    this.peer.on('connection', (connection)=>{
                        if (this.is_connected) {
                            connection.send('Peer is already connected!');
                            connection.close()
                            return;
                        }
                        this.is_connected = true;
                        this.connection = connection;
                        this.connection.on('data', message_handler);
                        this.peer.on('error', error_handler);
                        this.connection.on('error', error_handler);
                        this.peer.on('close', on_close);
                        this.connection.on('close', on_dc);
                        on_connection();
                    });
                });
            } else {
                this.peer = NetworkClient.createPeer('', ()=>{
                    this.connection = this.peer.connect(the_id);
                    this.connection.on('open', ()=>{
                        this.connection.on('data', message_handler);
                        this.peer.on('error', error_handler);
                        this.connection.on('error', error_handler);
                        this.peer.on('close', on_close);
                        this.connection.on('close', on_dc);
                        this.is_connected = true;
                        on_connection();
                    });
                });
            }
        }
        sendMessage(data) {
            if (this.destroyed) {console.log("Peer has already been destroyed!"); return;}
            if (this.connection !== undefined && this.is_connected) {
                if (data === "!!!ping!!!") {this.ping(); return;}
                this.connection.send(data);
            } else {
                if (debug_level >= 1) {console.log(`Attempted to send ${data}, but the connection was not yet established!`);}
            }
        }

        destroy() {
            if (this.destroyed) {console.log("Peer has already been destroyed!"); return;}
            if (this.connection !== undefined && this.is_connected) {this.connection.close();}
            console.log("Peer destroyed!");
            this.peer.destroy();
            this.is_connected = false;
            this.peer = null;
            this.connection = undefined;
            this.destroyed = true;
        }
        ping() {
            this.last_ping = Date.now();
            this.connection.send("!!!ping!!!")
        }

        respond_ping() {
            this.sendMessage("!!!pong!!!")
        }
    }

    const noop = () => {};

    function on_data_received(data) {
        if (data === "!!!ping!!!") {network_client.respond_ping();}
        if (data == "!!!pong!!!") {
            if (debug_level >= 1) {
                console.log(`Ping: ${Date.now() - network_client.last_ping} ms (roundtrip)`)
            }
        }
        const actual_key = network_key + 'recv';
        window.dispatchEvent(new CustomEvent("networkrecvdata", {"detail" : data}));
        if (debug_level >= 3) {console.log(`Received ${data}`);}
        let curr = localStorage.getItem(actual_key);
        if (curr === undefined || curr == null) {curr = "";}
        localStorage.setItem(actual_key, curr + data + MESSAGE_ENDER);
    }

    function error_handler(error) {
        const data = error.toString()
        const actual_key = network_key + 'err';
        window.dispatchEvent(new CustomEvent("networkerr", {"detail" : data}));
        if (debug_level >= 1) {console.log(data);}
        let curr = localStorage.getItem(actual_key);
        if (curr === undefined || curr == null) {curr = "";}
        localStorage.setItem(actual_key, curr + data + MESSAGE_ENDER);
    }

    function on_connection() {
        const data = "Connected!";
        const actual_key = network_key + 'conn';
        window.dispatchEvent(new CustomEvent("networkconn", {"detail" : data}));
        if (debug_level >= 1) {console.log(data);}
        let curr = localStorage.getItem(actual_key);
        if (curr === undefined || curr == null) {curr = "";}
        localStorage.setItem(actual_key, curr + data + MESSAGE_ENDER);
    }

    function on_close() {
        const data = "Connection closed";
        const actual_key = network_key + 'close';
        window.dispatchEvent(new CustomEvent("networkclose", {"detail" : data}));
        if (debug_level >= 1) {console.log(data);}
        let curr = localStorage.getItem(actual_key);
        if (curr === undefined || curr == null) {curr = "";}
        localStorage.setItem(actual_key, curr + data + MESSAGE_ENDER);
    }

    function on_dc() {
        const data = "Connection disconnected";
        const actual_key = network_key + 'dc';
        window.dispatchEvent(new CustomEvent("networkdc", {"detail" : data}));
        if (debug_level >= 1) {console.log(data);}
        let curr = localStorage.getItem(actual_key);
        if (curr === undefined || curr == null) {curr = "";}
        localStorage.setItem(actual_key, curr + data + MESSAGE_ENDER);
    }

    let network_client = new NetworkClient(is_host, peerId, on_data_received, error_handler, on_close, on_dc, on_connection);
    console.log("Created a client(" + is_host.toString() + ")");
    window.addEventListener('NetworkSendData', (event) => {
        const data = event.detail.data
        const net_key = event.detail.net_key
        if (net_key === network_key) {
            network_client.sendMessage(data);
        }
    });
    window.addEventListener('NetworkDisconnect', (event) => {
        const net_key = event.detail.net_key
        if (net_key === network_key) {
            network_client.sendMessage(data);
        }
    });
    window.addEventListener('NetworkClose', (event) => {
        const net_key = event.detail.net_key
        if (net_key === network_key) {
            network_client.destroy();
        }
    });
    })