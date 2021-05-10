var sender_id = document.getElementById("sender_id").value;
//var user_id = document.getElementById("user_id").value;
var sender_name = document.getElementById("sender_name").value;
var sender_email = document.getElementById("sender_email").value;
var sender_photo = document.getElementById("sender_photo").value;
var friend_name = document.getElementById("friend_name").value;
var friend_email = document.getElementById("friend_email").value;
var message = document.getElementById("message");
var submitBtn = document.getElementById("submitBtn");
var chat_log = document.getElementById("chat_log");
var online = document.getElementById("online");
var st = document.getElementById("st");

var attachBtn = document.getElementById("attachment-btn");

var semail = sender_email;
var femail = friend_email;

sender_email = sender_email.replace(/\./g,"ddoott");
friend_email = friend_email.replace(/\./g,"ddoott");

// console.log('notification/' + sender_email + '/' + friend_email);
// console.log(friend_email.replace(/ddoott/g,"."));

firebase.database().ref('notification/' + sender_email + '/' + friend_email).remove();

firebase.database().ref('status/' + friend_email + '_' + sender_email).remove();
firebase.database().ref('status/' + friend_email + '_' + sender_email).push().set({
    user: sender_email,
    time: new Date().getTime(),
    online: 'online'
});

function submitClick(){
    var messageText = message.value;
    var time = new Date().getTime();
    if (messageText.length > 0){
        firebase.database().ref('messages/' + sender_email + '_' + friend_email).push().set({
            message: messageText,
            image:'',
            video:'',
            lat:'',
            lon:'',
            time: new Date().getTime(),
            user:semail
        });
        firebase.database().ref('messages/' + friend_email + '_' + sender_email).push().set({
            message: messageText,
            image:'',
            video:'',
            lat:'',
            lon:'',
            time: new Date().getTime(),
            user:semail
        });
        firebase.database().ref('notification/' + friend_email + '/' + sender_email).remove();
        firebase.database().ref('notification/' + friend_email + '/' + sender_email).push().set({
            sender: semail,
            senderName: sender_name,
            msg: messageText,
            senderPhoto: sender_photo,
            time: new Date().getTime()
        });
        firebase.database().ref('status/' + friend_email + '_' + sender_email).remove();
        firebase.database().ref('status/' + friend_email + '_' + sender_email).push().set({
            sender: sender_name,
            time: new Date().getTime(),
            online: 'online'
        });
        document.getElementById("message").value = "";

        attachBtn.style.display = 'block';
        submitBtn.style.display = 'none';

    }else {
        window.alert("Please write something...");
    }
}

var monthes=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

var starCountRef = firebase.database().ref('messages/' + sender_email + '_' + friend_email);
starCountRef.on('child_added', function(snapshot) {
  var new_post = snapshot.val();
  var mes = new_post.message;
  var image = new_post.image;
  var video = new_post.video;
  var lat = new_post.lat;
  var lng = new_post.lon;

  if (mes.length > 0){
      var time = parseInt(new_post.time);

      var date = new Date(time);

      var seconds = date.getSeconds();
      var minutes = date.getMinutes();
      var hours = date.getHours();
//
      var year = date.getFullYear();
      var month = date.getMonth(); // beware: January = 0; February = 1, etc.
      var day = date.getDate();

      var ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12; // the hour '0' should be '12'
      minutes = minutes < 10 ? '0'+minutes : minutes;
      var timeStr = month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ' ' + ampm;

      var yearStr = year.toString();

      if(day < 10)
            timeStr = monthes[month] + " 0" + day + ", " + yearStr.substr(2, 2) + "' " + hours + ':' + minutes + ' ' + ampm;
        else
            timeStr = monthes[month] + " " + day + ", " + yearStr.substr(2, 2) + "' " + hours + ':' + minutes + ' ' + ampm;

    //   var oneMinuteMilliseconds = 60000;
    //   var oneHourMilliseconds = 3600000;
    //   var oneDayMilliseconds = 24*3600*1000;
    //   var oneMonthMilliseconds = oneDayMilliseconds*30;
    //   var now = Date.now();

    //   if(now - time < oneMinuteMilliseconds) timeStr = "Just now";
    //   if(oneMinuteMilliseconds <= now - time && now - time < oneHourMilliseconds) timeStr = String(parseInt((now - time)/(60000))) + "m ago";
    //   if(oneHourMilliseconds <= now - time && now - time < oneDayMilliseconds) timeStr = String(parseInt((now - time)/(3600000))) + "h ago";
    //   if(oneDayMilliseconds <= now - time && now - time < oneMonthMilliseconds) timeStr = String(parseInt((now - time)/(24*3600000))) + "d ago";

      var ul = document.getElementById("list");
      if (new_post.user == semail){
           var li = document.createElement("div");
           li.style.color = 'white';
           li.style.fontSize = '16';
           li.style.paddingRight = '15';
           li.style.paddingLeft = '15';
           li.style.paddingTop = '10';
           li.style.paddingBottom = '10';
           li.style.backgroundColor = '#2390f6';
           li.style.borderTopLeftRadius = '20px';
           li.style.borderTopRightRadius = '20px';
           li.style.borderBottomLeftRadius = '20px';
           li.style.borderBottomRightRadius = '0px';
           li.style.maxWidth = "500";
           li.style.display = 'inline-block';
           li.innerHTML = mes;
           li.style.textAlign = 'left';

           if (video.length > 0){
                if (!mes.includes("Please review the information. If you have questions, you can reply directly to the customer. If you want to accept or decline, please click here.")){
                    li.style.position = 'relative';
                    var mark = document.createElement("img");
                    mark.src = '/static/images/fileicon.png';
                    mark.style.width = '33';
                    mark.style.height = '35';
                    mark.style.position = 'absolute';
                    mark.style.top = '0px';
                    mark.style.left = '-40px';
                    li.appendChild(mark);

                    li.onclick = function(){
                        if (video.length > 0){
                            window.open(video);
                        }
                    }
                }
           }

           var ul2 = document.createElement("div");
           ul2.append(li);

           ul2.style.textAlign = 'right';
           ul.appendChild(ul2);

           var lli = document.createElement("div");
           lli.style.color = 'black';
           lli.style.fontSize = '12';
           lli.style.display = 'inline-block';
           lli.innerHTML = timeStr;
           lli.style.textAlign = 'left';
           var ull2 = document.createElement("div");

           ull2.append(lli);
           ull2.style.textAlign = 'right';

           ul.appendChild(ull2);
      }else {
           var li = document.createElement("div");
           li.style.textAlign = 'left';
           li.style.color = 'black';
           li.style.fontSize = '16';
           li.style.paddingRight = '15';
           li.style.paddingLeft = '15';
           li.style.paddingTop = '10';
           li.style.paddingBottom = '10';
           li.style.backgroundColor = '#e0ccff';
           li.style.borderTopLeftRadius = '20px';
           li.style.borderTopRightRadius = '20px';
           li.style.borderBottomLeftRadius = '0px';
           li.style.borderBottomRightRadius = '20px';
           li.style.maxWidth = "500";
           li.style.display = 'inline-block';
           li.innerHTML = mes;

           if (video.length > 0){
                if (!mes.includes("Please review the information. If you have questions, you can reply directly to the customer. If you want to accept or decline, please click here.")){
                    li.style.position = 'relative';
                    var mark = document.createElement("img");
                    mark.src = '/static/images/fileicon.png';
                    mark.style.width = '33';
                    mark.style.height = '35';
                    mark.style.position = 'absolute';
                    mark.style.top = '0px';
                    mark.style.right = '-40px';
                    li.appendChild(mark);
                    li.onclick = function(){
                        if (video.length > 0){
                            window.open(video);
                        }
                    }
                }
           }

           if (mes.includes("Please review the information. If you have questions, you can reply directly to the customer. If you want to accept or decline, please click here.")){
                var index = mes.indexOf("Thanks");
                li.innerHTML = mes.substring(0, index-1) + "\n";

                var accept = document.createElement('a');
                accept.style.textAlign = 'center';
                accept.style.color = 'red';
                accept.style.fontSize = '18';
                accept.style.paddingRight = '10';
                accept.style.paddingLeft = '10';
                accept.style.paddingTop = '10';
                accept.style.paddingBottom = '10';
                accept.style.backgroundColor = '#e0d0f6';
                accept.style.display = 'inline-block';

                accept.setAttribute('href',"javascript:accept('accepted', lat, lng, video);");
                accept.innerHTML = "Accept";

                li.appendChild(accept);

                accept.onclick = function(){
                   send_msg('accepted', lat, lng, video);
                }

                var decline = document.createElement("a");
                decline.style.textAlign = 'center';
                decline.style.color = 'red';
                decline.style.fontSize = '18';
                decline.style.paddingRight = '10';
                decline.style.paddingLeft = '10';
                decline.style.paddingTop = '10';
                decline.style.paddingBottom = '10';
                decline.style.backgroundColor = '#e0d0f6';
                decline.style.display = 'inline-block';
                decline.style.marginLeft = "50";
                decline.setAttribute('href',"javascript:accept('declined', lat, lng, video);");
                decline.innerHTML = "Decline";
                li.appendChild(decline);

                decline.onclick = function(){
                   send_msg('declined', lat, lng, video);
                }

                var footer = document.createElement("div");
                footer.style.textAlign = 'left';
                footer.style.color = 'black';
                footer.style.fontSize = '16';
                footer.style.paddingRight = '10';
                footer.style.paddingLeft = '10';
                footer.style.paddingTop = '10';
                footer.style.paddingBottom = '10';
                footer.style.backgroundColor = '#e0d0f6';
                footer.style.maxWidth = "300";
                footer.style.display = 'inline-block';
                footer.innerHTML = mes.substring(index, mes.length);
                li.appendChild(footer);
           }

           var ul3 = document.createElement("div");
           ul3.append(li);

           ul.appendChild(ul3);

           var llli = document.createElement("div");
           llli.style.textAlign = 'left';
           llli.style.color = 'black';
           llli.style.fontSize = '12';

           llli.style.display = 'inline-block';
           llli.innerHTML = timeStr;
           var ull3 = document.createElement("div");

           ull3.append(llli);
           ul.appendChild(ull3);
      }

      chat_log.scrollTop = chat_log.scrollHeight;
  }
  if(image.length > 0){
      var time = parseInt(new_post.time);

      var date = new Date(time);

      var seconds = date.getSeconds();
      var minutes = date.getMinutes();
      var hours = date.getHours();
//
      var year = date.getFullYear();
      var month = date.getMonth(); // beware: January = 0; February = 1, etc.
      var day = date.getDate();

      var ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12; // the hour '0' should be '12'
      minutes = minutes < 10 ? '0'+minutes : minutes;
      var timeStr = month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ' ' + ampm;

      var yearStr = year.toString();

      if(day < 10)
            timeStr = monthes[month] + " 0" + day + ", " + yearStr.substr(2, 2) + "' " + hours + ':' + minutes + ' ' + ampm;
        else
            timeStr = monthes[month] + " " + day + ", " + yearStr.substr(2, 2) + "' " + hours + ':' + minutes + ' ' + ampm;

    //   var oneMinuteMilliseconds = 60000;
    //   var oneHourMilliseconds = 3600000;
    //   var oneDayMilliseconds = 24*3600*1000;
    //   var oneMonthMilliseconds = oneDayMilliseconds*30;
    //   var now = Date.now();

    //   if(now - time < oneMinuteMilliseconds) timeStr = "Just now";
    //   if(oneMinuteMilliseconds <= now - time && now - time < oneHourMilliseconds) timeStr = String(parseInt((now - time)/(60000))) + "m ago";
    //   if(oneHourMilliseconds <= now - time && now - time < oneDayMilliseconds) timeStr = String(parseInt((now - time)/(3600000))) + "h ago";
    //   if(oneDayMilliseconds <= now - time && now - time < oneMonthMilliseconds) timeStr = String(parseInt((now - time)/(24*3600000))) + "d ago";

      var ul = document.getElementById("list");
      if (new_post.user == semail){

           var img = document.createElement("img");

           img.style.width = "200";
           img.style.height = "auto";
           img.style.maxHeight = "200";
           img.style.borderTopLeftRadius = '10px';
           img.style.borderTopRightRadius = '10px';
           img.style.borderBottomLeftRadius = '10px';
           img.style.borderBottomRightRadius = '0px';
           img.style.display = 'inline-block';
           if(image.length > 1500)img.src = "data:image/jpeg;base64,"+image;
           else img.src = image;
           img.classList.add("cropping");

           var li = document.createElement("div");

           li.style.paddingRight = '10';
           li.style.paddingLeft = '10';
           li.style.paddingTop = '10';
           li.style.paddingBottom = '10';
           li.style.backgroundColor = '#2390f6';
           li.style.borderTopLeftRadius = '20px';
           li.style.borderTopRightRadius = '20px';
           li.style.borderBottomLeftRadius = '20px';
           li.style.borderBottomRightRadius = '0px';
           li.style.maxWidth = "300";
           li.style.display = 'inline-block';
           li.appendChild(img);

           if (video.length > 0){
                li.style.position = 'relative';
                var mark = document.createElement("img");
                mark.src = '/static/images/playbutton.png';
                mark.style.width = '40';
                mark.style.height = '30';
                mark.style.position = 'absolute';
                mark.style.top = '40%';
                mark.style.right = '40%';
                li.appendChild(mark);
           }

           li.onclick = function(){
              if (video.length > 0){
                  window.open(video, '_blank');
              }else{
                  if (lat.length > 0){
                      window.location.href = "/show_chatloc?latlng=" + String(lat) + "_" + String(lng);
                  }
                  else{
                      window.open(image, '_blank');
                  }
              }
           }

           var ul2 = document.createElement("div");

           ul2.append(li);
           ul2.style.textAlign = 'right';
           ul.appendChild(ul2);

           var lli = document.createElement("div");
           lli.style.color = 'black';
           lli.style.fontSize = '12';
           lli.style.display = 'inline-block';
           lli.innerHTML = timeStr;
           lli.style.textAlign = 'left';
           var ull2 = document.createElement("div");

           ull2.append(lli);
           ull2.style.textAlign = 'right';

           ul.appendChild(ull2);
      }else {

           var img = document.createElement("img");

           img.style.width = "200";
           img.style.height = "auto";
           img.style.maxHeight = "200";
           img.style.borderTopLeftRadius = '10px';
           img.style.borderTopRightRadius = '10px';
           img.style.borderBottomLeftRadius = '0px';
           img.style.borderBottomRightRadius = '10px';
           img.style.display = 'inline-block';
           if(image.length > 1500)img.src = "data:image/jpeg;base64,"+image;
           else img.src = image;
           img.classList.add("cropping");

           var li = document.createElement("div");

           li.style.paddingRight = '10';
           li.style.paddingLeft = '10';
           li.style.paddingTop = '10';
           li.style.paddingBottom = '10';
           li.style.backgroundColor = '#e0ccff';
           li.style.borderTopLeftRadius = '20px';
           li.style.borderTopRightRadius = '20px';
           li.style.borderBottomLeftRadius = '0px';
           li.style.borderBottomRightRadius = '20px';
           li.style.maxWidth = "300";
           li.style.display = 'inline-block';
           li.appendChild(img);

           if (video.length > 0){
                li.style.position = 'relative';
                var mark = document.createElement("img");
                mark.src = '/static/images/playbutton.png';
                mark.style.width = '40';
                mark.style.height = '30';
                mark.style.position = 'absolute';
                mark.style.top = '40%';
                mark.style.right = '40%';
                li.appendChild(mark);
           }

           li.onclick = function(){
              if (video.length > 0){
                   window.open(video, '_blank');
              }else{
                  if (lat.length > 0){
                      window.location.href = "/show_chatloc?latlng=" + String(lat) + "_" + String(lng);
                  }
                  else{
                      window.open(image, '_blank');
                  }
              }
           }

           var ul3 = document.createElement("div");

           ul3.append(li);
           ul.appendChild(ul3);

           var llli = document.createElement("div");
           llli.style.textAlign = 'left';
           llli.style.color = 'black';
           llli.style.fontSize = '12';

           llli.style.display = 'inline-block';
           llli.innerHTML = timeStr;
           var ull3 = document.createElement("div");

           ull3.append(llli);
           ul.appendChild(ull3);
      }

      chat_log.scrollTop = chat_log.scrollHeight;
  }

  chat_log.scrollTop = chat_log.scrollHeight;

});


var starCountRef = firebase.database().ref('status/' + sender_email + '_' + friend_email);
starCountRef.on('child_added', function(snapshot) {
    var new_status = snapshot.val();
    var onoff = new_status.online;
    if (onoff == 'offline'){
        var time = parseInt(new_status.time);
        var date = new Date(time);

        var seconds = date.getSeconds();
        var minutes = date.getMinutes();
        var hours = date.getHours();

        var year = date.getFullYear();
        var month = date.getMonth(); // beware: January = 0; February = 1, etc.
        var day = date.getDate();

        var ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // the hour '0' should be '12'
        minutes = minutes < 10 ? '0'+minutes : minutes;
        var timeStr = month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ' ' + ampm;

        var yearStr = year.toString();

          if(day < 10)
                timeStr = monthes[month] + " 0" + day + ", " + yearStr.substr(2, 2) + "' " + hours + ':' + minutes + ' ' + ampm;
            else
                timeStr = monthes[month] + " " + day + ", " + yearStr.substr(2, 2) + "' " + hours + ':' + minutes + ' ' + ampm;

        //   var oneMinuteMilliseconds = 60000;
        //   var oneHourMilliseconds = 3600000;
        //   var oneDayMilliseconds = 24*3600*1000;
        //   var oneMonthMilliseconds = oneDayMilliseconds*30;
        //   var now = Date.now();

        //   if(now - time < oneMinuteMilliseconds) timeStr = "Just now";
        //   if(oneMinuteMilliseconds <= now - time && now - time < oneHourMilliseconds) timeStr = String(parseInt((now - time)/(60000))) + "m ago";
        //   if(oneHourMilliseconds <= now - time && now - time < oneDayMilliseconds) timeStr = String(parseInt((now - time)/(3600000))) + "h ago";
        //   if(oneDayMilliseconds <= now - time && now - time < oneMonthMilliseconds) timeStr = String(parseInt((now - time)/(24*3600000))) + "d ago";

        online.innerHTML = 'Last seen at ' + timeStr;
        st.innerHTML = 'Offline';
        st.style.display = 'inline-block';
    }else {
        online.innerHTML = onoff;
        st.innerHTML = onoff;
        st.style.display = 'inline-block';
    }
});

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
    if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
        document.getElementById("photo").style.display = "block";
    } else {
        document.getElementById("photo").style.display = "none";
    }
}


//window.onload = function () {
//    if (typeof history.pushState === "function") {
//        history.pushState("jibberish", null, null);
//        window.onpopstate = function () {
//            if (confirm("Do you want to exit the room?")) {
//                firebase.database().ref('status/' + user_id + '_' + sender_id).remove();
//                firebase.database().ref('status/' + user_id + '_' + sender_id).push().set({
//                    sender: sender_name,
//                    time: new Date().getTime(),
//                    online: 'offline'
//                });
//                history.go(-1);
//            }
//        };
//
//    }
//};


function myFunction() {

    if(message.value.length > 0){
        firebase.database().ref('status/' + friend_email + '_' + sender_email).remove();
        firebase.database().ref('status/' + friend_email + '_' + sender_email).push().set({
            user: semail,
            time: new Date().getTime(),
            online: 'is typing...'
        });
    }else {
        firebase.database().ref('status/' + friend_email + '_' + sender_email).remove();
        firebase.database().ref('status/' + friend_email + '_' + sender_email).push().set({
            user: semail,
            time: new Date().getTime(),
            online: 'online'
        });
    }

    isTyping();
}


function isTyping(){

    if(message.value.length > 0){
        attachBtn.style.display = 'none';
        submitBtn.style.display = 'block';
    }else{
        attachBtn.style.display = 'block';
        submitBtn.style.display = 'none';
    }

    // alert('is typing...');

}



function okay(){
   var type = document.getElementById("type").value;
   var image = getBase64Image(document.getElementById("image_message"));
   var time = new Date().getTime();
   if (type == 'picture'){

       var progressBar = document.getElementById('gif');

        progressBar.style.display = 'block';
        document.getElementById("imageFrame").style.display = "none";

        var storageRef = firebase.storage().ref();

        var uploadTask = storageRef.child(file.name).put(file);
        uploadTask.on('state_changed', function(snapshot){
            // Observe state change events such as progress, pause, and resume
            // Get task progress, including the number of bytes uploaded and the total number of bytes to be uploaded
            var progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
            console.log('Upload is ' + progress + '% done');
            switch (snapshot.state) {
                case firebase.storage.TaskState.PAUSED: // or 'paused'
                    console.log('Upload is paused');
                    break;
                case firebase.storage.TaskState.RUNNING: // or 'running'
                    console.log('Upload is running');
                    break;
            }
        }, function(error) {
            // Handle unsuccessful uploads
        }, function() {
            // Handle successful uploads on complete
            // For instance, get the download URL: https://firebasestorage.googleapis.com/...
            var downloadURL = uploadTask.snapshot.downloadURL;

            if (image.length > 0){
                firebase.database().ref('messages/' + sender_email + '_' + friend_email).push().set({
                    message: '',
                    image: String(downloadURL),
                    video:'',
                    lat:'',
                    lon:'',
                    time: new Date().getTime(),
                    user:semail
                });
                firebase.database().ref('messages/' + friend_email + '_' + sender_email).push().set({
                    message: '',
                    image: String(downloadURL),
                    video:'',
                    lat:'',
                    lon:'',
                    time: new Date().getTime(),
                    user:semail
                });
                firebase.database().ref('notification/' + friend_email + '/' + sender_email).remove();
                firebase.database().ref('notification/' + friend_email + '/' + sender_email).push().set({
                    sender: semail,
                    senderName: sender_name,
                    msg: 'Shared a file',
                    senderPhoto: sender_photo,
                    time: new Date().getTime()
                });
                firebase.database().ref('status/' + friend_email + '_' + sender_email).remove();
                firebase.database().ref('status/' + friend_email + '_' + sender_email).push().set({
                    sender: sender_name,
                    time: new Date().getTime(),
                    online: 'online'
                });

                progressBar.style.display = 'none';
            }
        });
   }
   else if (type == 'video'){

//        var storageRef = firebase.storage().ref(file.name);
//        storageRef.put(file);
        var progressBar = document.getElementById('gif');

        progressBar.style.display = 'block';
        document.getElementById("imageFrame").style.display = "none";

        var thumbnail = getThumbImage(document.getElementById('videoresult'));

        var storageRef = firebase.storage().ref();

        var uploadTask = storageRef.child(file.name).put(file);
        uploadTask.on('state_changed', function(snapshot){
            // Observe state change events such as progress, pause, and resume
            // Get task progress, including the number of bytes uploaded and the total number of bytes to be uploaded
            var progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
            console.log('Upload is ' + progress + '% done');
            switch (snapshot.state) {
                case firebase.storage.TaskState.PAUSED: // or 'paused'
                    console.log('Upload is paused');
                    break;
                case firebase.storage.TaskState.RUNNING: // or 'running'
                    console.log('Upload is running');
                    break;
            }
        }, function(error) {
            // Handle unsuccessful uploads
        }, function() {
            // Handle successful uploads on complete
            // For instance, get the download URL: https://firebasestorage.googleapis.com/...
            var downloadURL = uploadTask.snapshot.downloadURL;

            firebase.database().ref('messages/' + sender_email + '_' + friend_email).push().set({
                message: '',
                image: thumbnail,
                video: String(downloadURL),
                lat:'',
                lon:'',
                time: new Date().getTime(),
                user:semail
            });
            firebase.database().ref('messages/' + friend_email + '_' + sender_email).push().set({
                message: '',
                image: thumbnail,
                video: String(downloadURL),
                lat:'',
                lon:'',
                time: new Date().getTime(),
                user:semail
            });
            firebase.database().ref('notification/' + friend_email + '/' + sender_email).remove();
            firebase.database().ref('notification/' + friend_email + '/' + sender_email).push().set({
                sender: semail,
                senderName: sender_name,
                msg: 'Shared a file',
                senderPhoto: sender_photo,
                time: new Date().getTime()
            });
            firebase.database().ref('status/' + friend_email + '_' + sender_email).remove();
            firebase.database().ref('status/' + friend_email + '_' + sender_email).push().set({
                sender: sender_name,
                time: new Date().getTime(),
                online: 'online'
            });

            progressBar.style.display = 'none';
        });
   }
   else if (type == 'map'){
        var lat = document.getElementById("lat").value;
        var lng = document.getElementById("lng").value;
        var image = getBase64Image(document.getElementById("image_message"));
        if (image.length > 0){
            firebase.database().ref('messages/' + sender_email + '_' + friend_email).push().set({
                message: '',
                image: image,
                video:'',
                lat:lat,
                lon:lng,
                time: new Date().getTime(),
                user:semail
            });
            firebase.database().ref('messages/' + friend_email + '_' + sender_email).push().set({
                message: '',
                image: image,
                video:'',
                lat:lat,
                lon:lng,
                time: new Date().getTime(),
                user:semail
            });
            firebase.database().ref('notification/' + friend_email + '/' + sender_email).remove();
            firebase.database().ref('notification/' + friend_email + '/' + sender_email).push().set({
                sender: semail,
                senderName: sender_name,
                msg: 'Shared a location',
                senderPhoto: sender_photo,
                time: new Date().getTime()
            });
            firebase.database().ref('status/' + friend_email + '_' + sender_email).remove();
            firebase.database().ref('status/' + friend_email + '_' + sender_email).push().set({
                sender: sender_name,
                time: new Date().getTime(),
                online: 'online'
            });
            document.getElementById("imageFrame").style.display = "none";
        }
   }
}

function getBase64Image(img) {
  var canvas = document.createElement("canvas");
  canvas.width = img.width;
  canvas.height = img.height;
  var ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  var dataURL = canvas.toDataURL("image/png");
  return dataURL.replace(/^data:image\/(png|jpg);base64,/, "");
}

function getThumbImage(video) {
  var canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  var ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  var dataURL = canvas.toDataURL("image/png");
  return dataURL.replace(/^data:image\/(png|jpg);base64,/, "");
}


function uploadFile(file){

        var progressBar = document.getElementById('gif');
        progressBar.style.display = 'block';

        var storageRef = firebase.storage().ref();

        var uploadTask = storageRef.child(file.name).put(file);
        uploadTask.on('state_changed', function(snapshot){
            // Observe state change events such as progress, pause, and resume
            // Get task progress, including the number of bytes uploaded and the total number of bytes to be uploaded
            var progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
            console.log('Upload is ' + progress + '% done');
            switch (snapshot.state) {
                case firebase.storage.TaskState.PAUSED: // or 'paused'
                    console.log('Upload is paused');
                    break;
                case firebase.storage.TaskState.RUNNING: // or 'running'
                    console.log('Upload is running');
                    break;
            }
        }, function(error) {
            // Handle unsuccessful uploads
        }, function() {
            // Handle successful uploads on complete
            // For instance, get the download URL: https://firebasestorage.googleapis.com/...
            var downloadURL = uploadTask.snapshot.downloadURL;

            firebase.database().ref('messages/' + sender_email + '_' + friend_email).push().set({
                message: 'Sent a file: ' + file.name,
                image: '',
                video: String(downloadURL),
                lat:'',
                lon:'',
                time: new Date().getTime(),
                user:semail
            });
            firebase.database().ref('messages/' + friend_email + '_' + sender_email).push().set({
                message: 'Sent a file: ' + file.name,
                image: '',
                video: String(downloadURL),
                lat:'',
                lon:'',
                time: new Date().getTime(),
                user:semail
            });
            firebase.database().ref('notification/' + friend_email + '/' + sender_email).remove();
            firebase.database().ref('notification/' + friend_email + '/' + sender_email).push().set({
                sender: semail,
                senderName: sender_name,
                msg: 'Shared a file',
                senderPhoto: sender_photo,
                time: new Date().getTime()
            });
            firebase.database().ref('status/' + friend_email + '_' + sender_email).remove();
            firebase.database().ref('status/' + friend_email + '_' + sender_email).push().set({
                sender: sender_name,
                time: new Date().getTime(),
                online: 'online'
            });

            progressBar.style.display = 'none';
        });
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function accept(sts, lat, lng, mailid){
 //   alert(sts);
}

function post(path, params, method) {
    method = method || "post"; // Set method to post by default if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        if(params.hasOwnProperty(key)) {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);

            form.appendChild(hiddenField);
        }
    }

    document.body.appendChild(form);
    form.submit();
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

var date = new Date();
var time = new Date().getTime();
var seconds = date.getSeconds();
var minutes = date.getMinutes();
var hours = date.getHours();
//
var year = date.getFullYear();
var month = date.getMonth(); // beware: January = 0; February = 1, etc.
var day = date.getDate();

var ampm = hours >= 12 ? 'PM' : 'AM';
hours = hours % 12;
hours = hours ? hours : 12; // the hour '0' should be '12'
minutes = minutes < 10 ? '0'+minutes : minutes;
var timeStr = month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ' ' + ampm;


      var yearStr = year.toString();

      if(day < 10)
            timeStr = monthes[month] + " 0" + day + ", " + yearStr.substr(2, 2) + "' " + hours + ':' + minutes + ' ' + ampm;
        else
            timeStr = monthes[month] + " " + day + ", " + yearStr.substr(2, 2) + "' " + hours + ':' + minutes + ' ' + ampm;

    //   var oneMinuteMilliseconds = 60000;
    //   var oneHourMilliseconds = 3600000;
    //   var oneDayMilliseconds = 24*3600*1000;
    //   var oneMonthMilliseconds = oneDayMilliseconds*30;
    //   var now = Date.now();

    //   if(now - time < oneMinuteMilliseconds) timeStr = "Just now";
    //   if(oneMinuteMilliseconds <= now - time && now - time < oneHourMilliseconds) timeStr = String(parseInt((now - time)/(60000))) + "m ago";
    //   if(oneHourMilliseconds <= now - time && now - time < oneDayMilliseconds) timeStr = String(parseInt((now - time)/(3600000))) + "h ago";
    //   if(oneDayMilliseconds <= now - time && now - time < oneMonthMilliseconds) timeStr = String(parseInt((now - time)/(24*3600000))) + "d ago";



var datetime = timeStr;

function send_msg(sts, lat, lng, video){
    var messageText = '';
    if (sts == 'accepted'){
        messageText = 'Hi, ' + friend_name + '\n' + sender_name + ' has accepted you ' +
            lat + ' with schedule of ' + lng + '\n' + 'Thanks\n' + datetime + '\n' + sender_name;
    }else if (sts == 'declined'){
        messageText = 'Hi, ' + friend_name + '\n' + sender_name + ' can\'t do you ' + lat + ' with your requested schedule of ' +
            lng + '\n' + 'Please select another time or another service provider.\n' + 'We apologize for the inconvenience\n' + datetime + '\n' + sender_name;
    }

    if (messageText.length > 0){
        firebase.database().ref('messages/' + sender_email + '_' + friend_email).push().set({
            message: messageText,
            image:'',
            video:'',
            lat: '',
            lon: '',
            time: new Date().getTime(),
            user:semail
        });
        firebase.database().ref('messages/' + friend_email + '_' + sender_email).push().set({
            message: messageText,
            image:'',
            video:'',
            lat: '',
            lon: '',
            time: new Date().getTime(),
            user:semail
        });
        firebase.database().ref('notification/' + friend_email + '/' + sender_email).remove();
        firebase.database().ref('notification/' + friend_email + '/' + sender_email).push().set({
            sender: semail,
            senderName: sender_name,
            msg: messageText,
            senderPhoto: sender_photo,
            time: new Date().getTime()
        });

        // var params = {
        //     'service': lat,
        //     'name': friend_name,
        //     'email': document.getElementById("friend_email").value,
        //     'service_reqdate': lng,
        //     'status': sts,
        //     'mailid': video
        // }
        // post("/acchat", params);
    }
}





//  var timeStr = '';
//
//  var currentdate = new Date();
//
//  var cseconds = currentdate.getSeconds();
//  var cminutes = currentdate.getMinutes();
//  var chours = currentdate.getHours();
//
//  var cyear = currentdate.getFullYear();
//  var cmonth = currentdate.getMonth(); // beware: January = 0; February = 1, etc.
//  var cday = currentdate.getDate();
//
//  if (year == cyear && month == cmonth && day == cday && hours == chours && minutes == cminutes){
//      timeStr = 'Just Now';
//  }
//  else if (year == cyear && month == cmonth && day == cday && hours == chours && minutes != cminutes)
//  {
//      timeStr = (cminute - minutes) + ' min ago';
//  }
//  else if (year == cyear && month == cmonth && day == cday && hours != chours){
//      timeStr = (chours - hours) + ' hr ago';
//  }
//  else if (year == cyear && month == cmonth && ((cday - day) == 1)){
//      var ampm = hours >= 12 ? 'PM' : 'AM';
//      hours = hours % 12;
//      hours = hours ? hours : 12; // the hour '0' should be '12'
//      minutes = minutes < 10 ? '0'+minutes : minutes;
//      timeStr = 'Yesterday' + ' ' + hours + ':' + minutes + ' ' + ampm;
//  }
//  else {
//      var ampm = hours >= 12 ? 'PM' : 'AM';
//      hours = hours % 12;
//      hours = hours ? hours : 12; // the hour '0' should be '12'
//      minutes = minutes < 10 ? '0'+minutes : minutes;
//      timeStr = month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ' ' + ampm;
//  }







