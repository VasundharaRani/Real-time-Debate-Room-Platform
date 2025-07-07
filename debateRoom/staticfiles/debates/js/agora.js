const appid = "b6b8a55634544a4890ab32d46623c2a2";
const token = null;
const CHANNEL = roomId;

let socket = null;
let client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
let localAudioTrack;
let remoteUsers = {};
let isMutedByModerator = false;
let isLocallyMuted = false;

document.addEventListener("DOMContentLoaded", () => {
  joinAgoraVoiceRoom();
  setupWebSocketControl();
});

async function joinAgoraVoiceRoom() {
  await client.join(appid, CHANNEL, token, null);

  if (myRole === "debater") {
    localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack();
    await client.publish([localAudioTrack]);
    console.log("Published mic");
  }

  client.on("user-published", async (user, mediaType) => {
    await client.subscribe(user, mediaType);
    if (mediaType === "audio") {
      remoteUsers[user.uid] = user;
      user.audioTrack.play();
    }
  });

  client.on("user-left", (user) => {
    delete remoteUsers[user.uid];
  });
}

async function leaveAgoraRoom() {
  try {
    if (localAudioTrack) {
      await localAudioTrack.stop();
      await localAudioTrack.close();
    }
    await client.leave();
    console.log("Left Agora channel");
  } catch (err) {
    console.error("Error leaving Agora:", err);
  }
}

function setupWebSocketControl() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/ws/room/${roomId}/control/`);

  socket.onopen = () => {
    console.log("WebSocket connected to control channel");
  };

  socket.onmessage = function (event) {
    const data = JSON.parse(event.data);

    if (data.type === "moderator-control" && data.target_user_id == currentUserId) {
      const icon = document.getElementById("debater-mute-icon");
      const option = document.querySelector(`#debater-select option[value='${data.target_user_id}']`);

      if (data.action === "mute" && localAudioTrack) {
        localAudioTrack.setEnabled(false);
        icon.className = "fas fa-microphone-slash";
        isMutedByModerator = true;
        isLocallyMuted = false;
        console.log("You were muted by the moderator.");
        if (option) option.setAttribute("data-muted", "true");
      } else if (data.action === "unmute" && localAudioTrack) {
        localAudioTrack.setEnabled(true);
        icon.className = "fas fa-microphone";
        isMutedByModerator = false;
        isLocallyMuted = false;
        console.log("You were unmuted by the moderator.");
        if (option) option.setAttribute("data-muted", "false");
      } else if (data.action === "kick") {
        alert("You have been kicked from the debate by the moderator.");
        leaveAgoraRoom();
        window.location.href = "/" + dashboardUrl.replace(/^\/+/g, "");
      }
    } else if (data.type === "self-unmute") {
      const option = document.querySelector(`#debater-select option[value='${data.user_id}']`);
      if (option) {
        option.setAttribute("data-muted", "false");
        updateControlButtons(); 
      }
    }
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
  };

  socket.onclose = () => {
    console.warn("WebSocket connection closed");
  };
}

function sendControl(action, userId) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    alert("WebSocket not connected.");
    console.warn("WebSocket not ready:", socket?.readyState);
    return;
  }

  console.log(`Sending control: ${action} to user: ${userId}`);
  socket.send(JSON.stringify({
    action: action,
    target_user_id: userId
  }));
}

function toggleDebaterMute() {
  if (!localAudioTrack) return;

  const icon = document.getElementById("debater-mute-icon");

  if (isMutedByModerator) {
    localAudioTrack.setEnabled(true);
    isMutedByModerator = false;
    isLocallyMuted = false;
    icon.className = "fas fa-microphone";
    console.log("Unmuted after being muted by moderator");
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "self-unmute", user_id: currentUserId }));
    }
    return;
  }

  isLocallyMuted = !isLocallyMuted;
  localAudioTrack.setEnabled(!isLocallyMuted);
  icon.className = isLocallyMuted ? "fas fa-microphone-slash" : "fas fa-microphone";
  console.log("Toggled self-mute");
}

function updateControlButtons() {
  const select = document.getElementById("debater-select");
  const selectedOption = select.options[select.selectedIndex];
  const isMuted = selectedOption.getAttribute("data-muted") === "true";

  const muteBtn = document.getElementById("mute-icon-btn");
  muteBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
  muteBtn.disabled = isMuted; // disable if already muted

  // Always assign handleMuteClick; don't allow unmuting from moderator
  muteBtn.onclick = handleMuteClick;

  document.getElementById("control-buttons").style.display = "inline-block";
}


function handleMuteClick() {
  const select = document.getElementById("debater-select");
  const userId = select.value;

  sendControl("mute", userId);
  select.options[select.selectedIndex].setAttribute("data-muted", "true");
  updateControlButtons();
}

function handleKickClick() {
  const select = document.getElementById("debater-select");
  const userId = select.value;
  sendControl("kick", userId);
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}