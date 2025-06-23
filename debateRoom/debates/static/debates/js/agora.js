const appid = "b6b8a55634544a4890ab32d46623c2a2";
const token = null;
const CHANNEL = "{{ room.id }}";

let client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
let localAudioTrack;

async function joinAgoraVoiceRoom() {
  try {
    await client.join(appid, CHANNEL, token, null);

    localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack();
    await client.publish([localAudioTrack]);

    console.log("Voice published to channel:", CHANNEL);

    // Listen for remote users
    client.on("user-published", async (user, mediaType) => {
      await client.subscribe(user, mediaType);
      if (mediaType === "audio") {
        user.audioTrack.play();
        console.log("Remote audio playing from", user.uid);
      }
    });

    client.on("user-left", user => {
      console.log("User left:", user.uid);
    });
  } catch (err) {
    console.error("Agora join error:", err);
  }
}

// Call the function after DOM loads
document.addEventListener("DOMContentLoaded", () => {
  joinAgoraVoiceRoom();
});

let isMuted = false;

// Mute/Unmute self
function toggleMute() {
  if (!localAudioTrack) return;
  if (isMuted) {
    localAudioTrack.setEnabled(true);
    isMuted = false;
    document.getElementById("mute-btn").innerText = "Mute";
  } else {
    localAudioTrack.setEnabled(false);
    isMuted = true;
    document.getElementById("mute-btn").innerText = "Unmute";
  }
}