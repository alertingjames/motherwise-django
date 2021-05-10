var vgroup = document.getElementById("group").value;
var name = document.getElementById("sender_name").value;
var s_id = document.getElementById("sender_id").value;
var s_avatar = document.getElementById("sender_photo").value;

const main = async () => {
    /* Events handlers */
    VoxeetSDK.conference.on('streamAdded', (participant, stream) => {
        if (stream.type === 'ScreenShare') return addScreenShareNode(stream);
        addVideoNode(participant, stream);
        addParticipantNode(participant);
    });

    VoxeetSDK.conference.on('streamRemoved', (participant, stream) => {
        if (stream.type === 'ScreenShare') return removeScreenShareNode();
        removeVideoNode(participant);
        removeParticipantNode(participant);
    });

    try {
        var externalId = String(s_id) + String(s_id);
        console.log("Admin ExternalID: " + externalId);
        await VoxeetSDK.initialize('DV8XrUh4iZwxMsEmakvvyg==', '3nv7mIpIJZeB-NfzEQxUPLtHU0oSugtV1IC7k4wtiqs=');
        await VoxeetSDK.session.open({ name: name, externalId: externalId, avatarUrl: s_avatar });
        initUI();
    } catch (e) {
        alert('Something went wrong : ' + e);
    }
}

main();

// function shareManagerParticipantID(participantID){
//     firebase.database().ref('gv' + vgroup).remove();
//     firebase.database().ref('gv' + vgroup).push().set({
//         participantID: participantID
//     });
// }