fetchInject([
  'https://www.gstatic.com/firebasejs/4.10.0/firebase.js'
]).then(() => {
  console.log('Imported1')
})

fetchInject([
  'https://www.gstatic.com/firebasejs/4.10.0/firebase-messaging.js'
]).then(() => {
  console.log('Imported2')
})

// Initialize Firebase
var config = {
    apiKey: "AIzaSyDveaXbV1HHMREyZzbvQe53BJEHVIRCf14",
    authDomain: "motherwise-1585202524394.firebaseapp.com",
    databaseURL: "https://motherwise-1585202524394.firebaseio.com",
    projectId: "motherwise-1585202524394",
    storageBucket: "motherwise-1585202524394.appspot.com",
    messagingSenderId: "805720875706",
    appId: "1:805720875706:web:1e90b519b4cf8ca0f69883",
    measurementId: "G-TLGYEHY3TK"
};

firebase.initializeApp(config);
// Retrieve Firebase Messaging object.
const messaging = firebase.messaging();
messaging.usePublicVapidKey("BJ8Ofk7OYF5yY2j9_3WLryhVm2uwzIzivO1ICkR2NBsmGFgsjUrJgsIN9DKWRCQ8vwKOn7XfR0lP29K3njjmTnA");

// messaging.requestPermission()
// .then(function(){
//     console.log('Have permission');
//     return messaging.getToken();
// })
// .then(function(token){
//     console.log(token);
// })
// .then(function(err){
//     console.log('Error occured: ' + err);
// })

// if ('serviceWorker' in navigator) {
// navigator.serviceWorker.register('/static/js/firebase-messaging-sw.js')
//   .then(function(registration) {
//     console.log('Registration successful, scope is:', registration.scope);
//   }).catch(function(err) {
//     console.log('Service worker registration failed, error:', err);
//   });
// }

// Get Instance ID token. Initially this makes a network call, once retrieved
// subsequent calls to getToken will return from cache.
messaging.getToken().then((currentToken) => {
  if (currentToken) {
    console.log(currentToken);
  } else {
    // Show permission request.
    console.log('No Instance ID token available. Request permission to generate one.');
    // Show permission UI.
  }
}).catch((err) => {
  console.log('An error occurred while retrieving token. ', err);
});













































