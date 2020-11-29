
setInterval(function() {
  var today = new Date();
  var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
  var date = today.getFullYear() + '/' + String(today.getMonth() + 1).padStart(2, '0') + '/' + String(today.getDate()).padStart(2, '0');
  time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
  var elTime = document.getElementById("time");
  elTime.textContent = time;
  // console.log(time);
}, 31);

// const videoElement = document.querySelector('video');
// const videoSelect = document.querySelector('select#videoSource');
const videoElement = document.getElementById('video');
const videoSelect = document.getElementById('videoSource');
const selectors = [videoSelect];

const canvas = document.getElementById('canvas');
const canvas2 = document.getElementById('canvas2');
const takenphoto = document.getElementById('takenphoto');
const originalTakenphoto = document.getElementById('originalTakenPhoto');
const cardInfo = document.getElementById('cardsInfo');
const formInfo = document.getElementById('formInfo');

const takebutton = document.getElementById("takebutton");
const submitButton = document.getElementById("submitbutton");
const showGameStep = document.getElementById("showGameStep");


function gotDevices(deviceInfos) {
  const values = selectors.map(select => select.value);
  selectors.forEach(select => {
    while (select.firstChild) {
      select.removeChild(select.firstChild);
    }
  });
  for (let i = 0; i !== deviceInfos.length; ++i) {
    const deviceInfo = deviceInfos[i];
    const option = document.createElement('option');
    option.value = deviceInfo.deviceId;
    if (deviceInfo.kind === 'videoinput') {
      option.text = deviceInfo.label || `camera ${videoSelect.length + 1}`;
      videoSelect.appendChild(option);
    } else {
      console.log('Some other kind of source/device: ', deviceInfo);
    }
  }
  selectors.forEach((select, selectorIndex) => {
    if (Array.prototype.slice.call(select.childNodes).some(n => n.value === values[selectorIndex])) {
      select.value = values[selectorIndex];
    }
  });
}

function handleMediaDevicesError(error) {
  console.log('navigator.MediaDevices.getUserMedia error: ', error.message, error.name);
}

navigator.mediaDevices.enumerateDevices().then(gotDevices).catch(handleMediaDevicesError);

function clearphoto() {
  takenphoto.setAttribute("style", "display:none");
  submitButton.setAttribute("style", "display:none");
  cardInfo.value = "";
  showGameStep.innerHTML = "Submit Game Info"
}

function gotStream(stream) {
  window.stream = stream;
  videoElement.srcObject = stream;

  canvas.setAttribute('width', videoElement.videoWidth);
  canvas.setAttribute('height', videoElement.videoHeight);

  clearphoto();

  return navigator.mediaDevices.enumerateDevices();
}

function videoStart() {
  if (window.stream) {
    window.stream.getTracks().forEach(track => {
      track.stop();
    });
  }
  const videoSource = videoSelect.value;
  const constraints = {
    video: {deviceId: videoSource ? {exact: videoSource} : undefined},
    audio: false
  };
  navigator.mediaDevices.getUserMedia(constraints).then(gotStream).then(gotDevices).catch(handleMediaDevicesError);
}

videoSelect.onchange = videoStart;

videoStart();

function buttonsStart(){
  takebutton.addEventListener('click', function(ev){
    var promiseSendPicture = sendPicture(null);

    promiseSendPicture
    .then(function(respPost){
      var data = JSON.parse(respPost);
      var foundCards = data["found_cards"];
      var detectionsWithBoxes = data["detections_with_boxes"];
      var processedImage = data["prc_img"];
      var originalImage = data["original_img"];

      sessionStorage.setItem("detections_with_boxes", JSON.stringify(detectionsWithBoxes));

      updateTakenPhoto(processedImage, originalImage);
      assignFoundCards(foundCards);
    });
    ev.preventDefault();
  }, false);

  submitButton.addEventListener("click", function () {
    var promiseSendInfo = sendFormInfo(originalTakenphoto);

    promiseSendInfo
    .then(function(respPost){
      console.log(respPost);
      var data = JSON.parse(respPost);
      showGameStep.innerHTML = "Submit Game Info for Step " + data["gameStep"];
    });
    takenphoto.setAttribute("style", "display:none");
    submitButton.setAttribute("style", "display:none");
    cardInfo.value = "";
  });
}

buttonsStart();

function sendPicture(width){
  var context = canvas.getContext('2d');

  var height;
  if (width) {
    height = videoElement.videoHeight / (videoElement.videoWidth/width);
    if (isNaN(height)) {
      height = width / (4/3);
    }
  }
  else {
    height = videoElement.videoHeight;
    width = videoElement.videoWidth;
  }

  canvas.width = width;
  canvas.height = height;
  context.drawImage(videoElement, 0, 0, width, height);

  return new Promise(function(resolve, reject) {
    canvas.toBlob(function(blob) {
      var fd = new FormData();
      fd.set('video', blob);

      $.ajax({
        url: "/img",
        type : "POST",
        processData: false,
        contentType: false,
        data : fd,
        dataType: "text",
      })
      .done(function(respPost) {
        resolve(respPost)
      })
      .fail(function(data) {
        console.log(data);
      });
    })
  })
}

function assignFoundCards(foundCardsArray){
  cardInfo.value = foundCardsArray.join(";");
}

function toFormFromElems(elems){
  return new Promise(function(resolve, reject){
    var fd = new FormData();

    for (var i = 0, elem; elem = elems[i++];){
      // console.log(elem.id + " -> " + elem.value);
      fd.set(String(elem.id), String(elem.value));
    }

    // console.log(fd);
    resolve(fd);
  })
}

function sendFormInfo(inputPhoto){
  var elems = formInfo.elements;

  return new Promise(function(resolve, reject) {
    var getFd = toFormFromElems(elems);

    getFd
    .then(function(fd){
      var context = canvas2.getContext('2d');

      var width = inputPhoto.width;
      var height = inputPhoto.height;

      canvas2.width = width;
      canvas2.height = height;
      context.drawImage(inputPhoto, 0, 0, width, height);

      canvas2.toBlob(function(blob){

        fd.set('img', blob);
        fd.set('detections_with_boxes', sessionStorage.getItem("detections_with_boxes"));

        $.ajax({
          url: "/updategame",
          type : "POST",
          processData: false,
          contentType: false,
          dataType: "text",
          data : fd
        })
        .done(function(respPost) {
          resolve(respPost)
        })
        .fail(function(data) {
          console.log("Post request from sendFormInfo failed.")
          console.log(data);
        });
      })
    })
  })
}

function updateTakenPhoto(processedImage, originalImage){
  if (processedImage){
    if (takenphoto.hasAttribute('style')){
      takenphoto.removeAttribute('style');
    }
    takenphoto.setAttribute('src', processedImage);
  }
  // else {
  //   var timestamp = (new Date()).getTime();
  //   takenphoto.setAttribute('src', "{{ url_for('main.feed') }}" + '?_=' + timestamp);
  // }
  if (originalImage){
    originalTakenphoto.setAttribute('src', originalImage);
  }
  if (submitButton.hasAttribute('style')){
    submitButton.removeAttribute('style');
  }
}
