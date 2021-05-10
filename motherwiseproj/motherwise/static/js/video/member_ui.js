const initUI = () => {
  const mainVideo = document.getElementById('main_video');
  const nameMessage = document.getElementById('name-message');
  const joinButton = document.getElementById('join-btn');
  const conferenceAliasInput = document.getElementById('alias-input');
  const leaveButton = document.getElementById('leave-btn');
  const startVideoBtn = document.getElementById('start-video-btn');
  const stopVideoBtn = document.getElementById('stop-video-btn');
//   const startScreenShareBtn = document.getElementById('start-screenshare-btn');
//   const stopScreenShareBtn = document.getElementById('stop-screenshare-btn');
//   const startRecordingBtn = document.getElementById('start-recording-btn');
//   const stopRecordingBtn = document.getElementById('stop-recording-btn');

  nameMessage.innerHTML = `You are logged in as ${name}`;
  joinButton.disabled = false;
  joinButton.style.display = "block";

  joinButton.onclick = () => {
      let conferenceAlias = conferenceAliasInput.value;

      /*
      1. Create a conference room with an alias
      2. Join the conference with its id
      */
      VoxeetSDK.conference.create({ alias: conferenceAlias })
          .then((conference) => VoxeetSDK.conference.join(conference, {}))
          .then(() => {
              joinButton.disabled = true;
              joinButton.style.display = "none";
              leaveButton.disabled = false;
              leaveButton.style.display = "block";
              startVideoBtn.style.display = "block";
              startVideoBtn.disabled = false;
              mainVideo.style.display = "none";
            //   startScreenShareBtn.disabled = false;
            //   startRecordingBtn.disabled = false;
          })
          .catch((e) => console.log('Something wrong happened : ' + e))
  };

  leaveButton.onclick = () => {
      VoxeetSDK.conference.leave()
          .then(() => {
              joinButton.disabled = false;
              joinButton.style.display = "block";
              leaveButton.disabled = true;
              leaveButton.style.display = "none";
              startVideoBtn.style.display = "none";
              stopVideoBtn.style.display = "none";
              mainVideo.style.display = "block";
            //   startScreenShareBtn.disabled = true;
            //   stopScreenShareBtn.disabled = true;
          })
          .catch((err) => {
              console.log(err);
          });
  };

  startVideoBtn.onclick = () => {
      VoxeetSDK.conference.startVideo(VoxeetSDK.session.participant)
          .then(() => {
              startVideoBtn.disabled = true;
              startVideoBtn.style.display = "none";
              stopVideoBtn.disabled = false;
              stopVideoBtn.style.display = "block";
              mainVideo.style.display = "none";
          });
  };

  stopVideoBtn.onclick = () => {
      VoxeetSDK.conference.stopVideo(VoxeetSDK.session.participant)
          .then(() => {
              stopVideoBtn.disabled = true;
              stopVideoBtn.style.display = "none";
              startVideoBtn.disabled = false;
              startVideoBtn.style.display = "block";
          });
  };

//   startScreenShareBtn.onclick = () => {
//       VoxeetSDK.conference.startScreenShare()
//           .then(() => {
//               startScreenShareBtn.disabled = true;
//               stopScreenShareBtn.disabled = false;
//           })
//           .catch((e) => console.log(e))
//   };

//   stopScreenShareBtn.onclick = () => {
//       VoxeetSDK.conference.stopScreenShare()
//           .then(() => {
//               startScreenShareBtn.disabled = false;
//               stopScreenShareBtn.disabled = true;
//           })
//           .catch((e) => console.log(e))
//   };

//   startRecordingBtn.onclick = () => {
//       let recordStatus = document.getElementById('record-status');
//       VoxeetSDK.recording.start()
//           .then(() => {
//               recordStatus.innerText = 'Recording...';
//               startRecordingBtn.disabled = true;
//               stopRecordingBtn.disabled = false;
//           })
//           .catch((err) => {
//               console.log(err);
//           })
//   };

//   stopRecordingBtn.onclick = () => {
//       let recordStatus = document.getElementById('record-status');
//       VoxeetSDK.recording.stop()
//           .then(() => {
//               recordStatus.innerText = '';
//               startRecordingBtn.disabled = false;
//               stopRecordingBtn.disabled = true;
//           })
//           .catch((err) => {
//               console.log(err);
//           })
//   };
};

const addVideoNode = (participant, stream) => {
  const videoMainContainer = document.getElementById('video-main-container');
  const videoContainer = document.getElementById('video-container');
  let videoNode = document.getElementById('video-' + participant.id);

  console.log(participant.id);

  if(!videoNode) {
      videoNode = document.createElement('video');
      videoNode.setAttribute('id', 'video-' + participant.id);
      if (participant.id === VoxeetSDK.session.participant.id) {
          videoContainer.appendChild(videoNode);
      }else{
          if (participant.info.externalId === adminParticipantID) {
              videoMainContainer.appendChild(videoNode);
          }else{
              videoContainer.appendChild(videoNode);
          }
      }

      videoNode.autoplay = 'autoplay';
      videoNode.muted = true;

      videoNode.onclick = goFullscreen;

  }

  navigator.attachMediaStream(videoNode, stream);
};

const removeVideoNode = (participant) => {
  let videoNode = document.getElementById('video-' + participant.id);

  if (videoNode) {
      videoNode.parentNode.removeChild(videoNode);
  }
};

const addParticipantNode = (participant) => {
  const participantsList = document.getElementById('participants-list');

  // if the participant is the current session user, don't add himself to the list
  if (participant.id === VoxeetSDK.session.participant.id) return;

  let participantNode = document.createElement('li');
  participantNode.setAttribute('id', 'participant-' + participant.id);
  participantNode.innerText = `${participant.info.name}`;

  participantsList.appendChild(participantNode);
};

const removeParticipantNode = (participant) => {
  let participantNode = document.getElementById('participant-' + participant.id);

  if (participantNode) {
      participantNode.parentNode.removeChild(participantNode);
  }
};

// const addScreenShareNode = (stream) => {
//   const screenShareContainer = document.getElementById('screenshare-container');
//   let screenShareNode = document.getElementById('screenshare');

//   if (screenShareNode) return alert('There is already a participant sharing his screen !');

//   screenShareNode = document.createElement('video');
//   screenShareNode.setAttribute('id', 'screenshare');
//   screenShareNode.autoplay = 'autoplay';
//   navigator.attachMediaStream(screenShareNode, stream);

//   screenShareContainer.appendChild(screenShareNode);
// }

// const removeScreenShareNode = () => {
//   let screenShareNode = document.getElementById('screenshare');

//   if (screenShareNode) {
//       screenShareNode.parentNode.removeChild(screenShareNode);
//   }
// }

function goFullscreen() {
    var element = document.getElementById(this.id);
    if (element.mozRequestFullScreen) {
        element.mozRequestFullScreen();
    } else if (element.webkitRequestFullScreen) {
        element.webkitRequestFullScreen();
    }
}
