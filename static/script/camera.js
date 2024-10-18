// Configure a few settings and attach camera
Webcam.set({
    width: 800, height: 600, image_format: 'jpeg', jpeg_quality: 90
});

Webcam.attach('#my_camera');

// preload shutter audio clip
var shutter = new Audio();
shutter.autoplay = true;
shutter.src = navigator.userAgent.match(/Chrome/) ? 'shutter.ogg' : 'shutter.mp3';

function take_snapshot() {
    document.getElementById('snapshot').disabled = true;
    document.getElementById('snapshot').value = "Please Wait";
    // play sound effect
    shutter.play();

    // take snapshot and get image data
    Webcam.snap(function (data_uri) {
        // display results in page
        document.getElementById('my_camera').innerHTML = '<img src="' + data_uri + '"/>';
        var chosen_style = document.getElementById('neural-style').value
        var computing_device = document.getElementById('computing-device').value
        const formData = new FormData();
        formData.append("webcam", data_uri);
        formData.append("neural-style", chosen_style)
        formData.append("computing-device", computing_device)

        // After snap, image will be sent along with the desired style
        // I'm not using Webcam.upload since it only uploads the image without any other data.
        fetch('/render_style', {
            method: 'POST',
            body: formData,
            redirect: 'follow'
        }).then((response)=>{         
            if(response.redirected){
                window.location.href = response.url;
            }
        }) 
    });
}
