// eslint-disable-next-line no-unused-vars,complexity
function submitSignupForm() {
    var requiredFields = $(".required-field");
    var fieldPassword = $(".field-password");
    var fieldConfirmPassword = $(".field-confirm-password");

    var signupForm = $("#signup-form");
    var isDataValid = true;

    var passwordInputBox = fieldPassword[0].lastElementChild;
    var confirmPasswordInputBox = fieldConfirmPassword[0].lastElementChild;

    var disabledFields = document.querySelectorAll("input:disabled, select:disabled");

    for (let field = 0; field < requiredFields.length; field++) {
        requiredFields[field].style.borderColor = "#E3E3E3";

        if (requiredFields[field].value === "") {
            isDataValid = false;
            requiredFields[field].style.borderColor = "#D32D2D";
            // eslint-disable-next-line no-undef
            showToast("Please update all mandatory fields");
        } else if (requiredFields[field].type === "tel") {
            // eslint-disable-next-line no-undef
            if (!isValidTelNumber(requiredFields[field].value)) {
                isDataValid = false;
                requiredFields[field].style.borderColor = "#D32D2D";
                // eslint-disable-next-line no-undef
                showToast("Please enter a valid Phone Number");
            }
        }
    }

    if (passwordInputBox.value !== confirmPasswordInputBox.value) {
        isDataValid = false;
        passwordInputBox.style.borderColor = "#D32D2D";
        confirmPasswordInputBox.style.borderColor = "#D32D2D";
        // eslint-disable-next-line no-undef
        showToast("Password and Confirm Password should match");
    } else if (isDataValid) {
        for (var i = 0; i < disabledFields.length; i++) {
            disabledFields[i].disabled = false;
        }
        signupForm.submit();
    }
}
