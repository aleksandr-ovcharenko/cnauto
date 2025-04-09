fetch("https://cn-auto-backend.onrender.com/api/cars")
    .then(response => response.json())
    .then(data => console.log(data));