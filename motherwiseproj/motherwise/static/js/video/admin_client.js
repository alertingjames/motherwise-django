var name = document.getElementById("sender_name").value;
var g_id = document.getElementById("group").value;

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
        await VoxeetSDK.initialize('ZWtmMDBiMjByNzkzdQ==', 'MnM3NXBkcjZzazhzMjBmbXI5OXMwNnAxMG8=');
        await VoxeetSDK.session.open({ name: name });
        initUI();
    } catch (e) {
        alert('Something went wrong : ' + e);
    }
}

main();

function shareManagerParticipantID(participantID){
    firebase.database().ref('gv' + g_id).remove();
    firebase.database().ref('gv' + g_id).push().set({
        participantID: participantID
    });
}