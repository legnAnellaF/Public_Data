const query = new URLSearchParams(window.location.search).get('q') || 
              document.querySelector('#query')?.value;

if (query) {
    fetch("http://localhost:8000/api/widget", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({query: query})
    })
    .then(res => res.json())
    .then(data => console.log("위젯 데이터 수신:", data));
}
