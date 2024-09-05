// eslint-disable-next-line no-unused-vars
function validateDOB(selectedDate) {
    var today = new Date();
    var inputDate = new Date(selectedDate);

    if (inputDate > today) {
        document.getElementById("dob-error").style.display = "block";
        document.getElementById("birthdate").value = "";
    } else {
        document.getElementById("dob-error").style.display = "none";
    }
}
