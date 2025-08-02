const appid = "0a14d71d6058422ba7a61fb92ce5da16";
const token = null;
const CHANNEL = roomId;

let socket = null;
let client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
let localAudioTrack;
let remoteUsers = {};
let isMutedByModerator = false;
let isLocallyMuted = false;

// Join and setup on load
document.addEventListener("DOMContentLoaded", () => {
  joinAgoraVoiceRoom();
  setupWebSocketControl();
});

// Join Agora voice room
async function joinAgoraVoiceRoom() {
  await client.join(appid, CHANNEL, token, null);

  if (myRole === "debater") {
    localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack();
    await client.publish([localAudioTrack]);
    console.log("Microphone published");
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

// Leave Agora room (used when kicked)
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

// Setup WebSocket for moderator control
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
        if (option) option.setAttribute("data-muted", "true");
        console.log("You were muted by the moderator.");
      } else if (data.action === "unmute" && localAudioTrack) {
        localAudioTrack.setEnabled(true);
        icon.className = "fas fa-microphone";
        isMutedByModerator = false;
        isLocallyMuted = false;
        if (option) option.setAttribute("data-muted", "false");
        console.log("🎙️ You were unmuted by the moderator.");
      } else if (data.action === "kick") {
        alert("You have been kicked from the debate by the moderator.");
        leaveAgoraRoom();
        window.location.href = "/" + dashboardUrl.replace(/^\/+/, "");
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
    console.warn("WebSocket closed. Retrying in 3s...");
    setTimeout(setupWebSocketControl, 3000);
  };
}

// Send moderator action over WebSocket
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

// Debater's mute toggle
async function toggleDebaterMute() {
  if (!localAudioTrack) return;

  const icon = document.getElementById("debater-mute-icon");

  if (isMutedByModerator) {
    await localAudioTrack.setEnabled(true);
    isMutedByModerator = false;
    isLocallyMuted = false;
    icon.className = "fas fa-microphone";
    console.log(" Unmuted after moderator mute");
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "self-unmute", user_id: currentUserId }));
    }
    return;
  }

  isLocallyMuted = !isLocallyMuted;
  await localAudioTrack.setEnabled(!isLocallyMuted);
  icon.className = isLocallyMuted ? "fas fa-microphone-slash" : "fas fa-microphone";
  console.log("Toggled self-mute");
}

// Update moderator's mute button UI based on selection
function updateControlButtons() {
  const select = document.getElementById("debater-select");
  if (!select || select.selectedIndex < 0) return;

  const selectedOption = select.options[select.selectedIndex];
  const isMuted = selectedOption.getAttribute("data-muted") === "true";

  const muteBtn = document.getElementById("mute-icon-btn");
  muteBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
  muteBtn.disabled = false; // Always allow moderator to try again

  muteBtn.onclick = handleMuteClick;

  const controlWrapper = document.getElementById("control-buttons");
  if (controlWrapper) controlWrapper.style.display = "inline-block";
}

// Moderator mute action
function handleMuteClick() {
  const select = document.getElementById("debater-select");
  const userId = select.value;

  sendControl("mute", userId);
  select.options[select.selectedIndex].setAttribute("data-muted", "true");
  updateControlButtons();
}

// Moderator kick action
function handleKickClick() {
  const select = document.getElementById("debater-select");
  const userId = select.value;
  sendControl("kick", userId);
}

// CSRF helper for future fetch use
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