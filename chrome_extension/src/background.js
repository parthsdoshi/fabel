function postData(url = ``, data = {}) {
  // Default options are marked with *
    return fetch(url, {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        mode: "cors", // no-cors, cors, *same-origin
        cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
        credentials: "omit", // include, *same-origin, omit
        headers: {
            "Content-Type": "application/json"
        },
        redirect: "follow", // manual, *follow, error
        referrer: "no-referrer", // no-referrer, *client
        body: JSON.stringify(data), // body data type must match "Content-Type" header
    })
    .then(response => response.json()); // parses JSON response into native Javascript objects 
}

chrome.downloads.onChanged.addListener((downloadDelta) => {
    console.log(downloadDelta)
    if ("state" in downloadDelta) {
        if (downloadDelta.state.current == "complete") {
            query = {"id": downloadDelta.id}
            chrome.downloads.search(query, (downloadItemArray) => {
                downloadItem = downloadItemArray[0]
                console.log(downloadItem)
                postData(`http://localhost:4994/rcv`, downloadItem)
                .then(data => console.log(JSON.stringify(data))) // JSON-string from `response.json()` call
                .catch(error => console.error(error));
            })
        }
    }
})
