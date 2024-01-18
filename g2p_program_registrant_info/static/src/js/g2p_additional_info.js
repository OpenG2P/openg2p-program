/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {markup, useState} from "@odoo/owl";
import {TextField} from "@web/views/fields/text/text_field";
import {useService} from "@web/core/utils/hooks";
import {registry} from "@web/core/registry";

export class G2PAdditionalInfoWidget extends TextField {
    setup() {
        super.setup();
        this.state = useState({recordClicked: false});
        this.notification = useService("notification");
    }

    renderjson() {
        try {
            const valuesJsonOrig = this.props.record.data.additional_g2p_info;
            if (typeof valuesJsonOrig === "string" || valuesJsonOrig instanceof String) {
                const parsedValue = JSON.parse(valuesJsonOrig);
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
            this.notification.add(_t("Program Info"), {
                title: _t("Invalid Json Value"),
                type: "danger",
            });
            this.state.recordClicked = true;
            return {};
        }
    }

    flattenJson(object) {
        const jsonObject = JSON.parse(JSON.stringify(object));
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

export const JsonField = {
    component: G2PAdditionalInfoWidget,
    supportedTypes: ["json", "text", "html"],
};
registry.category("fields").add("g2p_addl_info_widget", G2PAdditionalInfoWidget);
