/** @odoo-module **/

import {FieldText} from "web.basic_fields";
import field_utils from "web.field_utils";
import fieldsRegistry from "web.field_registry";
import {qweb} from "web.core";

// eslint-disable-next-line no-undef
const markup = QWeb2.tools.markup;

field_utils.format.json = function (value) {
    return JSON.stringify(value, null, 2);
};
field_utils.parse.json = function (value) {
    return JSON.parse(value);
};

var G2PAdditionalInfoWidget = FieldText.extend({
    className: "o_field_g2p_addl_info",
    supportedFieldTypes: ["json", "text", "html"],
    tagName: "div",
    _renderReadonly: function () {
        try {
            let valuesJsonOrig = this.value;
            if (typeof valuesJsonOrig === "string" || valuesJsonOrig instanceof String) {
                valuesJsonOrig = JSON.parse(this.value);
            }

            if (Array.isArray(valuesJsonOrig)) {
                const sectionsJson = {};
                var self = this;
                valuesJsonOrig.forEach((element) => {
                    sectionsJson[element.name] = self.flattenJson(element.data);
                });
                return this.$el.html(
                    qweb.render("addl_info_template", {
                        sections: sectionsJson,
                    })
                );
            }

            const valuesJson = this.flattenJson(valuesJsonOrig);
            return this.$el.html(
                qweb.render("addl_info_each_table", {
                    flatJson: valuesJson,
                })
            );
        } catch (err) {
            console.error(err);
        }
        return this._super();
    },
    flattenJson: function (object) {
        const jsonObject = JSON.parse(JSON.stringify(object));
        for (const key in jsonObject) {
            if (!jsonObject[key]) continue;
            if (
                typeof jsonObject[key] === "object" &&
                "document_id" in jsonObject[key] &&
                "document_slug" in jsonObject[key]
            ) {
                const document_slug = jsonObject[key].document_slug;
                const host = window.location.origin;
                jsonObject[key] = markup(
                    `<a href="${host}/storage.file/${document_slug}" target="_blank">${document_slug}<span class="fa fa-fw fa-external-link"></span></a>`
                );
            } else if (typeof jsonObject[key] === "object") {
                jsonObject[key] = JSON.stringify(jsonObject[key]);
            }
        }
        return jsonObject;
    },
    _isSameValue: function (value) {
        return _.isEqual(value, this.value);
    },
});

fieldsRegistry.add("g2p_addl_info_widget", G2PAdditionalInfoWidget);

export {G2PAdditionalInfoWidget};
