const timerContainer = document.getElementById("otp-timer");
const timerElement = timerContainer.firstElementChild.firstElementChild;
const resendOTP = timerContainer.lastElementChild;

let timeRemaining = 120;

function updateTimer() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;

    timerElement.textContent = `${minutes.toString().padStart(2, "0")}:${seconds
        .toString()
        .padStart(2, "0")}`;

    timeRemaining--;

    if (timeRemaining < 0) {
        // eslint-disable-next-line no-use-before-define
        clearInterval(timerInterval);
        timerElement.textContent = "00:00";
        resendOTP.style.pointerEvents = "auto";
        resendOTP.style.color = "blue";
    }
}

let timerInterval = setInterval(updateTimer, 1000);

resendOTP.addEventListener("click", function () {
    timeRemaining = 120;
    resendOTP.style.pointerEvents = "none";
    resendOTP.style.color = "#ADB5BD";
    timerInterval = setInterval(updateTimer, 1000);
});

// eslint-disable-next-line no-unused-vars,complexity
function validateInput(input) {
    input.value = input.value.replace(/\D/g, "");
}
