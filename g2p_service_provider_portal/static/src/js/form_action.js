var voucherDetails = [];

fetch("/get_voucher_codes")
    .then(function (response) {
        if (response.ok) {
            return response.json();
        }
    })
    .then(function (data) {
        if (data) {
            voucherDetails = data;
        }
    });

// eslint-disable-next-line no-unused-vars,complexity
function reimbursementFormSubmitAction() {
    var formContainer = $(".s_website_form");
    var programForm = formContainer.find("form");
    var voucherInputField = $("[name='code']");
    var isValid = true;
    var program_id = $("#program_submit_id");
    var fileUploadSize = program_id[0].getAttribute("file-size");
    var beneficiayName = program_id[0].getAttribute("beneficiary");

    programForm[0].action = `/serviceprovider/submit/${program_id[0].getAttribute("program")}`;

    var modal = $("#SubmitModal");
    var requiredFields = $(".s_website_form_required");
    var inputFields = requiredFields.find("input");

    for (let i = 0; i < requiredFields.length; i++) {
        inputFields[i].style.borderColor = "#E3E3E3";
        if (inputFields[i].value === "") {
            isValid = false;
            modal[0].click(close);
            // eslint-disable-next-line no-undef
            showToast("Please update all mandatory fields.");
            inputFields[i].style.borderColor = "#DE514C";
        } else {
            for (let j = 0; j < voucherDetails.length; j++) {
                if (
                    voucherInputField[0] &&
                    voucherDetails[j].beneficiary_name === beneficiayName &&
                    voucherDetails[j].code === voucherInputField[0].value
                ) {
                    isValid = true;
                    break;
                } else if (voucherInputField[0]) {
                    isValid = false;
                    modal[0].click(close);
                    // eslint-disable-next-line no-undef
                    showToast("Please enter a valid voucher code.");
                    voucherInputField[0].style.borderColor = "#DE514C";
                } else {
                    isValid = false;
                    modal[0].click(close);
                    // eslint-disable-next-line no-undef
                    showToast(
                        "Voucher code or Actual Amount fields are not correctly mapped. Please re-check your form or Contact your Administrator."
                    );
                }
            }
        }
    }

    if (isValid) {
        // eslint-disable-next-line no-undef
        if (isFileAllowed(fileUploadSize)) {
            programForm.submit();
        } else {
            modal[0].click(close);
        }
    }
}
