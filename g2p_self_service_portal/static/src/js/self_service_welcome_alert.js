const alertBox = document.getElementById("alertbox");
const closeBtn = alertBox.querySelector(".closebtn");

if (!sessionStorage.getItem("alertShown")) {
    sessionStorage.setItem("alertShown", "false");
}

if (sessionStorage.getItem("alertShown") === "false") {
    alertBox.style.display = "block";
} else if (sessionStorage.getItem("alertShown") === "true") {
    alertBox.style.display = "none";
}

closeBtn.addEventListener("click", function () {
    sessionStorage.setItem("alertShown", "true");
    alertBox.style.display = "none";
});
