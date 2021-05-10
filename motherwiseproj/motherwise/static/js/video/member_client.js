var name = document.getElementById("sender_name").value;
var g_id = document.getElementById("group").value;
var s_id = document.getElementById("sender_id").value;
var s_avatar = document.getElementById("sender_photo").value;
// var admin_id = document.getElementById("admin_id").value;
var adminParticipantID = "{{admin.pk}}{{admin.pk}}";

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
        console.log("ExternalID: " + externalId);
        await VoxeetSDK.initialize('DV8XrUh4iZwxMsEmakvvyg==', '3nv7mIpIJZeB-NfzEQxUPLtHU0oSugtV1IC7k4wtiqs=');
        await VoxeetSDK.session.open({ name: name, externalId: externalId, avatarUrl: s_avatar });
        initUI();
    } catch (e) {
        alert('Something went wrong : ' + e);
    }
}

main();

// var participantID = "";

// var ref = firebase.database().ref('gv' + g_id);
// ref.on('child_added', function(snapshot) {
//   var val = snapshot.val();
//   participantID = val.participantID;

// });


















































