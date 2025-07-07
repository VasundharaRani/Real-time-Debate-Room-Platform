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
    console.log("Local stream tracks:", localStream.getAudioTracks());
    localStream.getAudioTracks().forEach(track => {
        console.log("Track enabled:", track.enabled);
    });
}

// websocket connection
function connectWebSocket() {
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/debate/${roomId}/`);
    // socket = new WebSocket(`ws://${window.location.host}/ws/debate/${roomId}/`);

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
            console.log("Received signal:", data);
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

        if (data.action === 'vote_update') {
            updateVoteChart(data.results);
        }
    };
}

// create peer connection and offer
async function createOffer(peerId) {
    const pc = new RTCPeerConnection(config);
    peers[peerId] = pc;

    localStream.getTracks().forEach(track => {
        pc.addTrack(track, localStream);
        console.log("Added track to peer connection:", track);
    });

    pc.onicecandidate = event => {
        if (event.candidate){
            console.log("Sending ICE candidate to", peerId, event.candidate);
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
        audio.play().catch(e => console.warn("Autoplay blocked:", e));
        console.log(`Remote audio track added from ${fromId}`, event.streams[0].getAudioTracks());


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
                console.log("Sending ICE candidate to", peerId, event.candidate);
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
            let audio = document.getElementById(`audio-${fromId}`);
            if (!audio) {
                audio = document.createElement('audio');
                audio.id = `audio-${fromId}`;
                audio.autoplay = true;
                document.body.appendChild(audio);
            }
            audio.srcObject = event.streams[0];
            console.log("Remote track received", event.streams);
            audio.play().catch(e => console.warn("Autoplay blocked:", e));

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
        console.log("Receiving ICE candidate from", fromId, signal.candidate);
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

function castVote(userId) {
    socket.send(JSON.stringify({
        action: "vote",
        voted_for: userId
    }));
}

function updateVoteChart(results) {
    for (const userId in results) {
        const percentage = results[userId];
        const bar = document.getElementById(`vote-bar-${userId}`);
        if (bar) {
            bar.style.width = `${percentage}%`;
            bar.textContent = `${percentage}%`;
        }
    }
}