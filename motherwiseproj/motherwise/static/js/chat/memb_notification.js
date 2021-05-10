var me_email = document.getElementById("me_email").value;
var ul = document.getElementById("list");
var keys = [];
me_email = me_email.replace(/\./g,"ddoott");
var starCountRef = firebase.database().ref('notification/' + me_email);
starCountRef.on('child_added', function(snapshot) {
  var key = snapshot.val();
  if (key){
    var key2 = getChildObj(key);
    var sender_name = key2.senderName;
//    window.alert(key2.message);
    var li = document.createElement("div");
    li.style.color = 'black';
    li.style.fontSize = '14';
    li.style.maxWidth = "auto";
    li.style.width = "auto";
    li.innerHTML = "<label style='font-size:14px; font-weight:600;'>" + sender_name + "</label>" + "<div style='color:gray; font-size:12px; margin-left:2px;'>" + timeConverter(Number(key2.time)) + "<label style='color:orange; width:auto; text-align:left; font-size:11px; margin-left:8px;'>View message</label>" + "</div>";
    // li.innerHTML = li.innerHTML + "<div style='font-size:12px;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;'>" + key2.msg + "</div>";
    li.style.textAlign = 'left';
    var ul2 = document.createElement("div");
    var img = document.createElement("img");
    if (key2.senderPhoto.length > 0) img.src = key2.senderPhoto;
    else img.src = "/static/images/manager.jpg";
    img.style.width = "40";
    img.style.height = "40";
    img.style.borderRadius = "50%";
    img.classList.add("cropping");
    img.style.cssFloat = 'right';
    ul2.appendChild(img);
    ul2.append(li);
    ul2.style.marginBottom = "1px";
    ul2.addEventListener('click', function (event) {
       var context = {
            'member_email': key2.sender
       }
       post('/mothers/to_chat/', context);
       console.log('/mothers/to_chat/');
    });
    ul.appendChild(ul2);
  }
//   else {
//       var lii = document.createElement("div");
//       lii.style.color = 'white';
//       lii.style.fontSize = '14';
//       lii.style.textAlign = 'center';
//       lii.innerHTML = "No message ...";
//       ul.append(lii);
//   }
});


function getChildObj (obj) {
    var obj2;
    for (var p in obj) {
        if (obj.hasOwnProperty(p)) {
            obj2 = obj[p];
        }
    }
    return obj2;
}

function getCookie(name) {
    console.log('getCookie');
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                    }
            }
    }
    console.log('cookie:' + cookieValue);
    return cookieValue;
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

   var hiddenField1 = document.createElement("input");
   hiddenField1.setAttribute("type", "hidden");
   hiddenField1.setAttribute("name", 'csrfmiddlewaretoken');
   hiddenField1.setAttribute("value", getCookie('csrftoken'));
   form.appendChild(hiddenField1);

   document.body.appendChild(form);
   form.submit();
}


function timeConverter(UNIX_timestamp){
  var a = new Date(UNIX_timestamp);
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var year = a.getFullYear();
  var month = months[a.getMonth()];
  var date = a.getDate();
  var hour = a.getHours();
  var min = a.getMinutes();
  var sec = a.getSeconds();
  var time = date + ' ' + month + ' ' + year + ' ' + hour + ':' + min + ':' + sec ;

  var yearStr = year.toString();

    if(date < 10)
        time = month + " 0" + date + ", " + yearStr.substr(2, 2) + "' " + hour + ':' + min;
    else
        time = month + " " + date + ", " + yearStr.substr(2, 2) + "' " + hour + ':' + min;

    // var oneMinuteMilliseconds = 60000;
    // var oneHourMilliseconds = 3600000;
    // var oneDayMilliseconds = 24*3600*1000;
    // var oneMonthMilliseconds = oneDayMilliseconds*30;
    // var now = Date.now();

    // if(now - UNIX_timestamp < oneMinuteMilliseconds) time = "Just now";
    // if(oneMinuteMilliseconds <= now - UNIX_timestamp && now - UNIX_timestamp < oneHourMilliseconds) time = String(parseInt((now - UNIX_timestamp)/(60000))) + "m ago";
    // if(oneHourMilliseconds <= now - UNIX_timestamp && now - UNIX_timestamp < oneDayMilliseconds) time = String(parseInt((now - UNIX_timestamp)/(3600000))) + "h ago";
    // if(oneDayMilliseconds <= now - UNIX_timestamp && now - UNIX_timestamp < oneMonthMilliseconds) time = String(parseInt((now - UNIX_timestamp)/(24*3600000))) + "d ago";
    console.log(time);

  return time;
}



















































