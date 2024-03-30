/** @odoo-module **/

import {markup, onMounted, useExternalListener, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {TextField} from "@web/views/fields/text/text_field";
import {useService} from "@web/core/utils/hooks";

export class G2PAdditionalInfoWidget extends TextField {
    setup() {
        super.setup();
        this.state = useState({recordClicked: false, noValue: false});
        this.notification = useService("notification");
        onMounted(() => this.validateValue());
        useExternalListener(window, "click", this.onclick);
        useExternalListener(window, "mouseup", this.onMouseup);
    }

    validateValue() {
        const val = this.props.record.data.program_registrant_info;

        if (val) {
            if ((!(val.charAt(0) === "{") && !(val.charAt(val.length - 1) === "}")) || !val) {
                this.state.noValue = true;
            }
        } else {
            this.state.noValue = true;
        }
    }

    onclick(event) {
        if (this.editingRecord && event.target.closest(".json-widget")) {
            this.state.recordClicked = true;
            this.state.noValue = true;
        }
        this.validateValue();
    }

    onMouseup(ev) {
        if (!ev.target.closest(".o_field_g2p_addl_info_widget textarea")) {
            this.state.recordClicked = false;
            this.state.noValue = false;
        }
        this.validateValue();
    }

    get editingRecord() {
        return !this.props.readonly;
    }

    renderjson() {
        try {
            const valuesJsonOrig = this.props.record.data.program_registrant_info;
            if (typeof valuesJsonOrig === "string" || valuesJsonOrig instanceof String) {
                const parsedValue = this.flattenJson(valuesJsonOrig);
                return parsedValue;
            }

            if (Array.isArray(valuesJsonOrig)) {
                const sectionsJson = {};
                valuesJsonOrig.forEach((element) => {
                    sectionsJson[element.name] = this.flattenJson(element.data);
                });
                return sectionsJson;
            }
            const valuesJson = this.flattenJson(valuesJsonOrig);
            return valuesJson;
        } catch (err) {
            console.error(err);
            this.notification.add(_t("Program Info"), {
                title: _t("Invalid Json Value"),
                type: "danger",
            });
            this.state.recordClicked = true;
            return {};
        }
    }

    flattenJson(object) {
        const jsonObject = JSON.parse(object);
        for (const key in jsonObject) {
            if (!jsonObject[key]) continue;
            if (
                Array.isArray(jsonObject[key]) &&
                jsonObject[key].length > 0 &&
                "document_id" in jsonObject[key][0] &&
                "document_slug" in jsonObject[key][0]
            ) {
                var documentFiles = "";
                for (var i = 0; i < jsonObject[key].length; i++) {
                    const document_slug = jsonObject[key][i].document_slug;
                    const host = window.location.origin;
                    if (i > 0) {
                        documentFiles += `<br />`;
                    }
                    documentFiles += `<a href="${host}/storage.file/${document_slug}" target="_blank">${document_slug}<span class="fa fa-fw fa-external-link"></span></a>`;
                }
                jsonObject[key] = markup(documentFiles);
            } else if (typeof jsonObject[key] === "object") {
                jsonObject[key] = JSON.stringify(jsonObject[key]);
            }
        }
        return jsonObject;
    }
}

G2PAdditionalInfoWidget.template = "addl_info_table";

export const G2PAdditionalInfoWidgets = {
    component: G2PAdditionalInfoWidget,
    supportedTypes: ["json", "text", "html"],
};
registry.category("fields").add("g2p_addl_info_widget", G2PAdditionalInfoWidgets);
