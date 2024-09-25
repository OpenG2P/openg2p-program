/** @odoo-module **/
import FormEditorRegistry from "@website/js/form_editor_registry";

FormEditorRegistry.add("apply_for_reimbursement", {
    formFields: [
        {
            type: "char",
            custom: false,
            required: true,
            placeholder: "Enter Voucher Code",
            fillWith: "code",
            name: "code",
            string: "Voucher Code",
        },
        {
            type: "float",
            custom: false,
            required: true,
            placeholder: "Enter Amount",
            fillWith: "initial_amount",
            name: "initial_amount",
            string: "Actual Amount",
        },
        {
            type: "binary",
            custom: true,
            required: true,
            name: "invoice",
            string: "Invoice",
        },
    ],
});
