function queue_NST_AI() {
    var chosen_style = document.getElementById('neural-style').value
    var computing_device = document.getElementById('computing-device').value
    const formData = new FormData();
    formData.append("neural-style", chosen_style)
    formData.append("computing-device", computing_device)
    fetch('/queue_ai', {
        method: 'POST',
        body: formData,
        redirect: 'follow'
    }).then((response)=>{         
        console.log(response);
    })
}

function get_images(){
    fetch('/get_neural_images', {
        method: 'GET',
    }).then((response)=>{
        // console.log(response);
        return response.json();
    }).then(json => {
        // console.log(json);
        var data = json.data;
        // console.log(data);
        imageParent = document.getElementById("progress");
        imageParent.innerHTML = "";
        for (let i = 0; i < data.length; i++){
            const div = document.createElement("div");
            const node = document.createElement("img");
            node.src = data[i];
            node.width = 180;
            div.appendChild(node);
            imageParent.appendChild(div);
        }
        console.log(data.length);
        if (data.length >= 12) {
            document.getElementById("continue").hidden = false;
        } 
    })
}

window.onload = queue_NST_AI();
setInterval(get_images, 2000);
