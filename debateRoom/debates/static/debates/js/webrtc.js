let localStream;
let peers = {};
let socket;
const roomId = ROOM_ID_FROM_TEMPLATE;
const userId = USER_ID_FROM_TEMPLATE;

// TURN/STUN Servers
const config = {
    iceServers : [
        { urls : 'stun:stun.l.google.com:19302'},
        {
            urls: 'turn:turn.debateplatform.com:3478',
            username: "TIMESTAMP_FROM_DJANGO",
            credential: "HMAC_BASED_CREDENTIAL"
        }
    ]
};

async function startMedia() {
    localStream = await navigator.mediaDevices.getUserMedia({audio : true, video: false});
}

// websocket connection
function connectWebSocket() {
    socket = new WebSocket('ws://${window.location.host}/ws/debate/${roomId}/');

    socket.onopen = () => {
        console.log("WebSocket Connected");
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.action === 'user-joined'){
            if(data.user_id !== userId){
                createOffer(data.user_id);
            }
        }

        if (data.action === 'signal'){
            handleSignal(data);
        }

        if (data.signal === 'user_left'){
            closeConnection(data.user_id);
        }

        if (data.action === 'mute'){
            if(data.user_id === userId){
                localStream.getAudioTracks().forEach(track => track.enabled = false);
                alert("You were muted by the moderator.");
            }
        }
    };
}

// create peer connection and offer
async function createOffer(peerId) {
    const pc = new RTCPeerConnection(config);
    peers[peerId] = pc;

    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));

    pc.onicecandidate = event => {
        if (event.candidate){
            socket.send(JSON.stringify({
                action : 'signal',
                target_id : peerId,
                signal_data : {
                    type : 'candidate',
                    candidate : event.candidate
                }
            }));
        }
    };

    pc.ontrack = event => {
        let audio = document.getElementById(`audio-${peerId}`);
        if (!audio) {
            audio = document.createElement('audio');
            audio.id = `audio-${peerId}`;
            audio.autoplay = true;
            document.body.appendChild(audio);
        }
        audio.srcObject = event.streams[0];
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    socket.send(JSON.stringify({
        action : 'signal',
        target_id : peerId,
        signal_data : {
            type : 'offer',
            sdp : offer
        }
    }));
}

// handle incoming signal
async function handleSignal(data) {
    const fromId = data.from_id;
    const signal = data.signal_data;

    let pc = peers[fromId];

    if(!pc) {
        pc = new RTCPeerConnection(config);
        peers[fromId] = pc;

        localStream.getTracks().forEach(track => pc.addTrack(track, localStream));

        pc.onicecandidate = event => {
            if (event.candidate){
                socket.send(JSON.stringify({
                    action : 'signal',
                    target_id : fromId,
                    signal_data : {
                        type : 'candidate',
                        candidate : event.candidate
                    }
                }));
            }
        };
    
        pc.ontrack = event => {
            let audio = document.getElementById(`audio-${peerId}`);
            if (!audio) {
                audio = document.createElement('audio');
                audio.id = `audio-${peerId}`;
                audio.autoplay = true;
                document.body.appendChild(audio);
            }
            audio.srcObject = event.streams[0];
        };
    }

    if (signal.type === 'offer'){
        await pc.setRemoteDescription(new RTCSessionDescription(signal.sdp));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        socket.send(JSON.stringify({
            action : 'signal',
            target_id : fromId,
            signal_data : {
                type : 'answer',
                sdp : answer
            }
        }));
    } else if (signal.type === 'answer'){
        await pc.setRemoteDescription(new RTCSessionDescription(signal.sdp));
    } else if (signal.type === 'candidate'){
        await pc.addIceCandidate(new RTCIceCandidate(signal.candidate));
    }
}

// close peer connection 
function closeConnection(peerId){
    if (peers[peerId]){
        peers[peerId].close();
        delete peers[peerId];
    }
}

// start everything
(async () => {
    await startMedia();
    connectWebSocket();
})();