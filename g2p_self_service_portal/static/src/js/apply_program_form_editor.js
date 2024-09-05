/** @odoo-module **/

import FormEditorRegistry from "@website/js/form_editor_registry";
import {_t} from "@web/core/l10n/translation";

FormEditorRegistry.add("apply_for_program", {
    formFields: [
        {
            type: "char",
            custom: false,
            required: false,
            string: _t("Dummy Field"),
        },
    ],
});
